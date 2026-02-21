# -*- coding: utf-8 -*-
"""Zeroconf (mDNS) service advertising for Home Assistant auto-discovery.

Registers Baby Buddy as ``_babybuddy._tcp.local.`` on the LAN so that
Home Assistant can detect it automatically without manual IP/port entry.
"""

import atexit
import logging
import signal
import socket
import threading

import dbsettings
from django.utils.translation import gettext_lazy as _
from zeroconf import ServiceInfo, Zeroconf as ZC

from babybuddy import VERSION
from babybuddy.config import config

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_babybuddy._tcp.local."
SERVICE_NAME = "Baby Buddy._babybuddy._tcp.local."


# ---------------------------------------------------------------------------
# Site Settings (dbsettings group)
# ---------------------------------------------------------------------------
# Defined here (not in site_settings.py) so the dbsettings module_name is
# "babybuddy.zeroconf" — this avoids attribute-name collisions with MQTT
# settings that also live at module level in "babybuddy.site_settings".
# ---------------------------------------------------------------------------


class ZeroconfSettings(dbsettings.Group):
    enabled = dbsettings.BooleanValue(
        default=True,
        description=_("Enable mDNS service advertising"),
        help_text=_(
            "Advertise Baby Buddy on the local network via mDNS (Zeroconf) "
            "so Home Assistant can auto-discover this instance."
        ),
    )
    advertised_port = dbsettings.PositiveIntegerValue(
        default=config.bb_port,
        description=_("Advertised port"),
        help_text=_(
            "The port that Home Assistant should connect to. If Baby Buddy "
            "is behind a reverse proxy, set this to the proxy's port."
        ),
    )
    instance_id = dbsettings.StringValue(
        default="",
        required=False,
        description=_("Instance ID"),
        help_text=_(
            "A stable UUID that uniquely identifies this Baby Buddy instance. "
            "Home Assistant uses this to track the instance across IP/port "
            "changes. Auto-generated on first run — do not change."
        ),
    )


# Module-level instance — dbsettings auto-discovers this.
zeroconf_settings = ZeroconfSettings(_("Zeroconf / mDNS"))


def _get_local_ip() -> str:
    """Return a LAN-routable IPv4 address for this host.

    Uses a UDP connect trick to determine which interface the OS would
    use to reach an external address, without actually sending any data.
    Falls back to ``socket.gethostbyname(socket.gethostname())``, then
    ``127.0.0.1`` as a last resort.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't actually send anything — just lets the OS pick the
            # outbound interface.
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        finally:
            s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    return "127.0.0.1"


def _get_zeroconf_settings():
    """Read Zeroconf settings from dbsettings (Site Settings page)."""
    return zeroconf_settings


class ZeroconfService:
    """Singleton mDNS service advertiser.

    Modelled after ``mqtt.client.MqttClient`` — call ``start()`` to begin
    advertising and ``stop()`` to unregister cleanly.
    """

    def __init__(self):
        self._zc = None
        self._info = None
        self._started = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        """Register the mDNS service on the LAN."""
        if self._started:
            return

        try:
            s = _get_zeroconf_settings()

            if not s.enabled:
                logger.info("Zeroconf mDNS advertising is disabled")
                return

            instance_id = s.instance_id or ""
            if not instance_id:
                import uuid

                from dbsettings.loading import set_setting_value

                instance_id = str(uuid.uuid4())
                set_setting_value("babybuddy.zeroconf", "", "instance_id", instance_id)
                logger.info("Auto-generated Zeroconf instance_id: %s", instance_id)

            port = s.advertised_port or config.bb_port
            path = config.sub_path
            ip = _get_local_ip()

            self._info = ServiceInfo(
                type_=SERVICE_TYPE,
                name=SERVICE_NAME,
                addresses=[socket.inet_aton(ip)],
                port=port,
                properties={
                    "instance_id": instance_id,
                    "path": path or "",
                    "version": VERSION,
                },
            )

            self._zc = ZC()
            self._zc.register_service(self._info, cooperating_responders=True)
            self._started = True

            # Register cleanup via atexit (clean interpreter exit) AND
            # signal handlers (SIGTERM/SIGINT from process managers).
            atexit.register(self.stop)
            self._install_signal_handlers()

            logger.info(
                "Zeroconf mDNS service registered: %s on %s:%s (id=%s)",
                SERVICE_NAME,
                ip,
                port,
                instance_id,
            )
        except Exception:
            logger.exception("Failed to register Zeroconf mDNS service")

    def stop(self):
        """Unregister the mDNS service and close the Zeroconf instance."""
        if not self._started:
            return
        try:
            logger.info("Unregistering Zeroconf mDNS service")
            if self._zc and self._info:
                self._zc.unregister_service(self._info)
            if self._zc:
                self._zc.close()
        except Exception:
            logger.exception("Error stopping Zeroconf mDNS service")
        finally:
            self._started = False
            self._zc = None
            self._info = None

    @property
    def is_started(self):
        """Return ``True`` if the mDNS service is currently registered."""
        return self._started

    def _install_signal_handlers(self):
        """Install SIGTERM/SIGINT handlers so ``stop()`` runs on kill.

        ``atexit`` only fires on clean interpreter exit.  Process managers
        (systemd, Docker, gunicorn, fuser -k) send SIGTERM, and Ctrl-C
        sends SIGINT.  We chain to the previous handler so Django's own
        shutdown logic still runs.
        """
        for sig in (signal.SIGTERM, signal.SIGINT):
            prev = signal.getsignal(sig)

            def _handler(signum, frame, _prev=prev):
                self.stop()
                # Chain to the previous handler (e.g. Django's).
                if callable(_prev):
                    _prev(signum, frame)
                elif _prev == signal.SIG_DFL:
                    signal.signal(signum, signal.SIG_DFL)
                    signal.raise_signal(signum)

            try:
                signal.signal(sig, _handler)
            except (OSError, ValueError):
                # Can't set signal handlers from non-main thread.
                pass

    def start_in_background(self):
        """Start the service in a daemon thread.

        ``register_service()`` can briefly block, so this keeps
        ``AppConfig.ready()`` fast.  The thread polls ``apps.ready``
        before touching the database — no arbitrary sleep.
        """

        def _guarded_start():
            import time

            from django.apps import apps

            # Wait until the app registry is fully populated.
            while not apps.ready:
                time.sleep(0.1)
            self.start()

        t = threading.Thread(target=_guarded_start, daemon=True)
        t.start()


# Module-level singleton.
zeroconf_service = ZeroconfService()
