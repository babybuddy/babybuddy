# -*- coding: utf-8 -*-
"""
Management command for cleanly removing a Baby Buddy plugin.

Usage:
    python manage.py remove_plugin <app_label>

This command:
1. Rolls back all of the plugin's migrations (dropping its tables)
2. Removes its entries from django_migrations so no stale history remains

Run this BEFORE uninstalling the plugin package or removing it from
INSTALLED_APPS. After running it you can safely uninstall/remove the plugin
and restart Baby Buddy with a clean database state.

Example (removing the books plugin):
    python manage.py remove_plugin books
    pip uninstall django-babybuddy-books
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Cleanly remove a Baby Buddy plugin: rolls back migrations and clears migration history."

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            help="The app_label of the plugin to remove (e.g. 'books').",
        )
        parser.add_argument(
            "--no-input",
            "--noinput",
            action="store_false",
            dest="interactive",
            help="Do not prompt for confirmation.",
        )

    def handle(self, *args, **options):
        app_label = options["app_label"]
        interactive = options["interactive"]

        # Confirm the app is actually installed.
        # apps.is_installed() checks by module name, not label — use app_configs
        # (keyed by label) to correctly handle plugins like books whose name is
        # 'babybuddy_books' but label is 'books'.
        from django.apps import apps

        if app_label not in apps.app_configs and not self._has_migration_history(
            app_label
        ):
            raise CommandError(
                f"No app with label '{app_label}' is installed and no migration "
                f"history found. Nothing to remove."
            )

        if interactive:
            self.stdout.write(
                self.style.ERROR(
                    f"\n⚠️  WARNING: This will PERMANENTLY AND IRREVERSIBLY DELETE all data "
                    f"stored by the '{app_label}' plugin.\n\n"
                    f"This includes every database record the plugin has created. "
                    f"There is NO undo. Back up your database before proceeding.\n"
                )
            )
            self.stdout.write(
                f"    Type '{app_label}' to confirm permanent deletion, or anything else to cancel:\n"
            )
            confirm = input("    > ")
            if confirm.strip() != app_label:
                raise CommandError("Aborted. No data was changed.")

        # Step 1: roll back all migrations (drops tables)
        if app_label in apps.app_configs:
            self.stdout.write(f"Rolling back migrations for '{app_label}'...")
            try:
                call_command(
                    "migrate", app_label, "zero", verbosity=1, interactive=False
                )
            except Exception as exc:
                raise CommandError(f"Migration rollback failed: {exc}") from exc
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"App '{app_label}' is not in INSTALLED_APPS — skipping migration "
                    f"rollback (tables may still exist in the database)."
                )
            )

        # Step 2: remove stale migration history entries
        removed = self._clear_migration_history(app_label)
        if removed:
            self.stdout.write(
                f"Removed {removed} migration history record(s) for '{app_label}'."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nPlugin '{app_label}' removed cleanly.\n"
                f"You can now uninstall the package and restart Baby Buddy."
            )
        )

    def _has_migration_history(self, app_label):
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM django_migrations WHERE app = %s",
                    [app_label],
                )
                return cursor.fetchone()[0] > 0
            except Exception:
                return False

    def _clear_migration_history(self, app_label):
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "DELETE FROM django_migrations WHERE app = %s", [app_label]
                )
                return cursor.rowcount
            except Exception:
                return 0
