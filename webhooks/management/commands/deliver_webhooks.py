# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from webhooks.delivery import deliver_pending


class Command(BaseCommand):
    help = "Deliver queued webhook events to their endpoints."

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=10,
            help="Seconds to wait for a response from an endpoint.",
        )

    def handle(self, *args, **options):
        delivered = deliver_pending(timeout=options["timeout"])
        self.stdout.write(
            self.style.SUCCESS(
                "Delivered {} event(s).".format(delivered)
                if delivered
                else "Nothing to deliver."
            )
        )
