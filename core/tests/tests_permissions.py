# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import Client as HttpClient
from django.test import TestCase
from django.urls import reverse


class PermissionCodenameTestCase(TestCase):
    """
    Guards against views and templates naming a permission that does not exist.

    Django's `has_perm()` and the `{% if perms.x.y %}` template tag both return
    `False` for an unknown codename instead of raising, so a typo silently
    denies access to every user who holds the *correct* permission. These tests
    only pass if the codenames used by the views and templates match the ones
    Django actually creates for the models.
    """

    @classmethod
    def setUpClass(cls):
        super(PermissionCodenameTestCase, cls).setUpClass()
        call_command("migrate", verbosity=0)
        cls.c = HttpClient()

    def _login_with(self, codenames):
        username = "perm-" + "-".join(sorted(codenames))[:20]
        user = get_user_model().objects.create_user(
            username=username,
            password="password",
            is_active=True,
        )
        user.user_permissions.set(
            Permission.objects.filter(
                content_type__app_label="core", codename__in=codenames
            )
        )
        # `has_perm()` caches per user instance, so re-fetch before using it.
        user = get_user_model().objects.get(pk=user.pk)
        self.c.force_login(user)
        return user

    def test_head_circumference_codenames_exist(self):
        codenames = (
            "view_headcircumference",
            "add_headcircumference",
            "change_headcircumference",
            "delete_headcircumference",
        )
        for codename in codenames:
            self.assertTrue(
                Permission.objects.filter(
                    content_type__app_label="core", codename=codename
                ).exists(),
                f"core.{codename} is not a permission Django creates",
            )

        # A user holding exactly those permissions must reach every view.
        self._login_with(codenames)
        for name in ("head-circumference-list", "head-circumference-add"):
            self.assertEqual(
                self.c.get(reverse(f"core:{name}")).status_code,
                200,
                f"{name} denied a user holding the real permission",
            )

    def test_tag_view_codename_exists(self):
        self.assertTrue(
            Permission.objects.filter(
                content_type__app_label="core", codename="view_tag"
            ).exists()
        )
        self._login_with(("view_tag",))
        self.assertEqual(
            self.c.get(reverse("core:tag-list")).status_code,
            200,
            "tag-list denied a user holding core.view_tag",
        )

    def test_views_do_not_reference_missing_permissions(self):
        """
        Every `core.<codename>` string in the view layer must exist.

        This catches typos in views that no request happens to exercise yet.
        """
        import inspect
        import re

        from django.contrib.auth.models import Permission

        from core import views as core_views
        from reports import views as reports_views

        existing = set(
            Permission.objects.values_list("content_type__app_label", "codename")
        )
        existing = {f"{app}.{codename}" for app, codename in existing}
        pattern = re.compile(r"core\.[a-z][a-z0-9_]*")
        missing = set()
        for module in (core_views, reports_views):
            source = inspect.getsource(module)
            for token in pattern.findall(source):
                # Only literal permission strings, not e.g. `core.models`.
                if token.split(".")[-1] in {"models", "views", "utils", "forms"}:
                    continue
                if token not in existing:
                    missing.add(token)
        self.assertEqual(
            missing,
            set(),
            f"views reference permissions that do not exist: {sorted(missing)}",
        )

    def test_templates_do_not_reference_missing_permissions(self):
        """
        Same check for `{% if perms.core.<codename> %}` in the templates.
        """
        import re
        from pathlib import Path

        from django.conf import settings

        existing = set(
            Permission.objects.values_list("content_type__app_label", "codename")
        )
        existing = {f"{app}.{codename}" for app, codename in existing}
        pattern = re.compile(r"perms\.(core\.[a-z][a-z0-9_]*)")
        missing = set()
        for app in ("babybuddy", "core", "dashboard", "reports"):
            templates = Path(settings.BASE_DIR) / app / "templates"
            if not templates.exists():
                continue
            for path in templates.rglob("*.html"):
                for token in pattern.findall(path.read_text(encoding="utf-8")):
                    if token not in existing:
                        missing.add(f"{token} ({path})")
        self.assertEqual(
            missing,
            set(),
            f"templates reference permissions that do not exist: {sorted(missing)}",
        )
