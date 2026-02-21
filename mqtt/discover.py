# -*- coding: utf-8 -*-
"""MQTT broker auto-discovery via mDNS, hostname probing, and subnet scan."""

import concurrent.futures
import ipaddress
import logging
import socket
import struct
import threading

logger = logging.getLogger(__name__)

WELL_KNOWN_HOSTS = [
    ("core-mosquitto", "Home Assistant add-on"),
    ("mosquitto", "Docker service"),
    ("mqtt", "DNS alias"),
    ("localhost", "Local"),
    ("host.docker.internal", "Docker host"),
]

DEFAULT_PORT = 1883
MDNS_TIMEOUT = 3
TCP_TIMEOUT = 2
SUBNET_SCAN_MAX = 254
# Minimal MQTT CONNECT packet (protocol level 4 = MQTT 3.1.1, clean session)
_MQTT_CONNECT = (
    b"\x10"  # CONNECT packet type
    b"\x11"  # remaining length = 17
    b"\x00\x04MQTT"  # protocol name
    b"\x04"  # protocol level 3.1.1
    b"\x02"  # flags: clean session
    b"\x00\x0a"  # keepalive 10s
    b"\x00\x05probe"  # client id "probe"
)


def _mqtt_probe(host, port=DEFAULT_PORT, timeout=TCP_TIMEOUT):
    """TCP connect and send a minimal MQTT CONNECT to verify the broker
    actually speaks MQTT (not just has an open port). Returns True on
    CONNACK, False otherwise."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.sendall(_MQTT_CONNECT)
        resp = s.recv(4)
        s.close()
        if len(resp) >= 4 and resp[0] == 0x20:
            return_code = resp[3]
            return return_code == 0
        return False
    except (socket.gaierror, socket.timeout, OSError, struct.error):
        return False


def _probe_host(host, port=DEFAULT_PORT):
    """MQTT-level probe. Returns the resolved IP if the broker accepts
    connections, or None."""
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return None
    if _mqtt_probe(ip, port):
        return ip
    return None


def _scan_mdns():
    """Browse for ``_mqtt._tcp.local.`` services. Returns a list of dicts."""
    results = []
    try:
        from zeroconf import Zeroconf, ServiceBrowser
    except ImportError:
        logger.debug("python-zeroconf not installed, skipping mDNS scan")
        return results

    found_event = threading.Event()

    class Listener:
        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if info:
                for addr in info.parsed_addresses():
                    results.append(
                        {
                            "host": addr,
                            "port": info.port,
                            "source": "mDNS",
                            "name": info.server.rstrip("."),
                        }
                    )
                    found_event.set()

        def remove_service(self, zc, type_, name):
            pass

        def update_service(self, zc, type_, name):
            pass

    zc = Zeroconf()
    try:
        ServiceBrowser(zc, "_mqtt._tcp.local.", Listener())
        found_event.wait(timeout=MDNS_TIMEOUT)
    finally:
        zc.close()

    return results


def _scan_hostnames():
    """Probe well-known hostnames in parallel. Returns a list of dicts."""
    results = []

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(WELL_KNOWN_HOSTS)
    ) as pool:
        futures = {
            pool.submit(_probe_host, host): (host, label)
            for host, label in WELL_KNOWN_HOSTS
        }
        for future in concurrent.futures.as_completed(futures):
            host, label = futures[future]
            ip = future.result()
            if ip is not None:
                results.append(
                    {
                        "host": host,
                        "port": DEFAULT_PORT,
                        "source": label,
                        "ip": ip,
                    }
                )

    return results


def _get_local_subnet():
    """Return the local IP and /24 network on the default route, or None.

    Uses a UDP connect to a public IP (no traffic sent) to let the OS
    pick the outbound interface, which works regardless of network setup.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
        s.close()
        network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
        return local_ip, network
    except Exception:
        return None, None


def _scan_subnet():
    """Scan the full local /24 for MQTT brokers. Uses a short timeout since
    all hosts are on the LAN — responsive hosts reply in <10ms."""
    local_ip, network = _get_local_subnet()
    if network is None:
        return []

    candidates = [
        str(ip) for ip in list(network.hosts())[:SUBNET_SCAN_MAX] if str(ip) != local_ip
    ]

    LAN_TIMEOUT = 0.5
    results = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(len(candidates), 50)
    ) as pool:
        futures = {
            pool.submit(_mqtt_probe, ip, DEFAULT_PORT, LAN_TIMEOUT): ip
            for ip in candidates
        }
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            if future.result():
                results.append(
                    {
                        "host": ip,
                        "port": DEFAULT_PORT,
                        "source": "Subnet scan",
                    }
                )

    return results


def discover_brokers():
    """Run all discovery methods and return a deduplicated list of brokers."""
    seen_ips = set()
    brokers = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        mdns_future = pool.submit(_scan_mdns)
        host_future = pool.submit(_scan_hostnames)
        subnet_future = pool.submit(_scan_subnet)

        for result in mdns_future.result():
            ip = result.get("ip") or result["host"]
            if ip not in seen_ips:
                seen_ips.add(ip)
                brokers.append(result)

        for result in host_future.result():
            ip = result.get("ip") or result["host"]
            if ip not in seen_ips:
                seen_ips.add(ip)
                brokers.append(result)

        for result in subnet_future.result():
            ip = result.get("ip") or result["host"]
            if ip not in seen_ips:
                seen_ips.add(ip)
                brokers.append(result)

    return brokers
