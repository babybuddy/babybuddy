# -*- coding: utf-8 -*-
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from webhooks.delivery import deliver_pending


def positive_seconds(value):
    seconds = float(value)
    if seconds <= 0:
        raise ValueError(value)
    return seconds


class Command(BaseCommand):
    help = "Deliver queued webhook events to their endpoints."

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=10,
            help="Seconds to wait for a response from an endpoint.",
        )
        parser.add_argument(
            "--every",
            type=positive_seconds,
            default=None,
            metavar="SECONDS",
            help=(
                "Keep running and deliver every SECONDS seconds instead of once. "
                "Checking an empty queue is one small query, so a second is fine."
            ),
        )

    def handle(self, *args, **options):
        if options["every"] is None:
            delivered = deliver_pending(timeout=options["timeout"])
            self.stdout.write(
                self.style.SUCCESS(
                    "Delivered {} event(s).".format(delivered)
                    if delivered
                    else "Nothing to deliver."
                )
            )
            return
        try:
            self.run_every(options["every"], options["timeout"])
        except KeyboardInterrupt:
            pass

    def run_every(self, seconds, timeout):
        """
        Deliver on a loop in one process, rather than starting Django again
        for every run.

        A run that fails is reported and the loop goes on: a database that is
        briefly unreachable, or still being migrated while the app starts, is
        not a reason for the worker to stop. Only a run that sent something is
        written out, so a quiet queue does not fill the log once a second.
        """
        while True:
            close_old_connections()
            try:
                delivered = deliver_pending(timeout=timeout)
            except Exception as error:
                self.stderr.write("Delivery run failed: {}".format(error))
            else:
                if delivered:
                    self.stdout.write(
                        self.style.SUCCESS("Delivered {} event(s).".format(delivered))
                    )
            time.sleep(seconds)
