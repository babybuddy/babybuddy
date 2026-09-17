from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from core import models


class CaregiverAccessTestCase(APITestCase):
    fixtures = ["tests.json"]

    def setUp(self):
        self.user = get_user_model().objects.create_user("caregiver-access")
        self.user.groups.add(
            Group.objects.get(name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"])
        )
        models.Medication.objects.create(
            child=models.Child.objects.first(), name="Test dose"
        )
        token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_api_scope_and_delete_boundaries(self):
        for model in (
            models.Feeding,
            models.DiaperChange,
            models.Sleep,
            models.Timer,
            models.Medication,
            models.Temperature,
            models.Weight,
            models.Note,
            models.TummyTime,
        ):
            with self.subTest(model=model.__name__):
                endpoint = reverse(f"api:{model._meta.model_name}-list")
                self.assertEqual(self.client.get(endpoint).status_code, 200)
                obj = model.objects.first()
                self.assertIsNotNone(obj)
                response = self.client.delete(f"{endpoint}{obj.pk}/")
                self.assertEqual(response.status_code, 403)
                self.assertTrue(model.objects.filter(pk=obj.pk).exists())

        for name in ("bmi", "height", "headcircumference", "pumping", "tag"):
            with self.subTest(model=name):
                endpoint = reverse(f"api:{name}-list")
                self.assertEqual(self.client.get(endpoint).status_code, 403)
                self.assertEqual(
                    self.client.post(endpoint, {}, format="json").status_code, 403
                )

        child = models.Child.objects.first()
        endpoint = reverse("api:child-detail", kwargs={"slug": child.slug})
        self.assertEqual(self.client.get(endpoint).status_code, 200)
        self.assertEqual(
            self.client.patch(endpoint, {"first_name": "Changed"}).status_code, 403
        )
        self.assertEqual(self.client.delete(endpoint).status_code, 403)

    def test_api_edit_allowed_entry(self):
        note = models.Note.objects.first()
        endpoint = reverse("api:note-detail", kwargs={"pk": note.pk})
        response = self.client.patch(
            endpoint, {"note": "Settled after lunch."}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertEqual(note.note, "Settled after lunch.")

    def test_deactivation_revokes_existing_api_key_and_web_session(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("api:feeding-list")).status_code, 200)
        self.assertEqual(self.client.get("/feedings/add/").status_code, 200)
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertIn(
            self.client.get(reverse("api:feeding-list")).status_code, (401, 403)
        )
        response = self.client.get("/feedings/add/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_web_scope_including_reports(self):
        self.client.force_login(self.user)
        child = models.Child.objects.first()
        for path in (
            "/feedings/add/",
            "/changes/add/",
            "/sleep/add/",
            "/timers/add/",
            "/medication/add/",
            "/temperature/add/",
            "/weight/add/",
            "/notes/add/",
            "/tummy-time/add/",
            "/user/settings/",
            reverse("dashboard:dashboard-child", kwargs={"slug": child.slug}),
            reverse("core:child", kwargs={"slug": child.slug}),
            reverse(
                "reports:report-medication-frequency-child", kwargs={"slug": child.slug}
            ),
            reverse("reports:report-weight-change-child", kwargs={"slug": child.slug}),
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        for path in (
            "/pumping/",
            "/pumping/add/",
            "/height/",
            "/height/add/",
            "/bmi/",
            "/head-circumference/",
            "/tags/",
            "/users/",
            "/users/add/",
            reverse(
                "reports:report-pumping-amounts-child", kwargs={"slug": child.slug}
            ),
            reverse("reports:report-height-change-child", kwargs={"slug": child.slug}),
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)
        for path in ("/settings/", "/admin/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn("login", response.url)
