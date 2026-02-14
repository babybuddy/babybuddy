# -*- coding: utf-8 -*-
"""
Create or fetch an API token for MCP / dev use.

Safety: Only run in a trusted environment. Anyone who can run manage.py can
get a token. The token is printed to stdout (terminal history, logs, or
copy-paste can leak it). Use -q to print only the token when capturing, e.g.:
  export BB_API_TOKEN=$(pipenv run python manage.py create_mcp_token -q)

Best practice: run once, set BB_API_TOKEN in your environment (e.g. Cursor MCP
server env or .env), then restart the MCP server. Never commit the token.

Example:

  pipenv run python manage.py create_mcp_token
  pipenv run python manage.py create_mcp_token --username admin
  pipenv run python manage.py create_mcp_token -q   # token only, for capture
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Get or create an API token for a user (for MCP / dev). Set BB_API_TOKEN to the output."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=None,
            help="User to get/create token for. Default: first superuser or first user.",
        )
        parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Print only the token (no extra message). Use when capturing, e.g. export BB_API_TOKEN=$(... create_mcp_token -q)",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options.get("username")
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"No user with username: {username!r}")
        else:
            user = (
                User.objects.filter(is_superuser=True).first() or User.objects.first()
            )
            if not user:
                raise CommandError(
                    "No user in database. Create one first (e.g. manage.py createuser)."
                )
        token, created = Token.objects.get_or_create(user=user)
        self.stdout.write(token.key)
        if not options.get("quiet") and options.get("verbosity", 1) > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\nToken for user {user.username!r} (created={created}). "
                    "Set BB_API_TOKEN to this value in your environment and restart the MCP server."
                )
            )
