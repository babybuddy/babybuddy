"""Web-request regression tests for permissions on care-entry side effects."""

from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.utils import timezone

from core import forms, models


class EntryPermissionsTestCase(TestCase):
    fixtures = ["tests.json"]
    timer_entries = (
        ("feedings", models.Feeding),
        ("sleep", models.Sleep),
        ("tummy-time", models.TummyTime),
        ("pumping", models.Pumping),
    )

    def setUp(self):
        self.child = models.Child.objects.first()
        self.user = get_user_model().objects.create_user(username="entry-caregiver")
        self.user.groups.add(
            Group.objects.get(name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"])
        )
        self.other = get_user_model().objects.create_user(username="timer-owner")
        # Pumping is deliberately excluded from the caregiver defaults.
        self.grant("add_pumping", "change_pumping")
        self.client.force_login(self.user)
        self.start = timezone.now() - timezone.timedelta(hours=2)
        self.end = self.start + timezone.timedelta(minutes=10)

    def grant(self, *codenames):
        for codename in codenames:
            self.user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label="core", codename=codename
                )
            )

    def entry_data(self, path):
        data = {
            "child": self.child.pk,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }
        if path == "feedings":
            data.update(type="formula", method="bottle", amount="50")
        elif path == "pumping":
            data["amount"] = "50"
        return data

    def timer(self, owner):
        # Distinct periods keep an earlier unexpected save from masking later cases.
        self.start -= timezone.timedelta(days=1)
        self.end -= timezone.timedelta(days=1)
        return models.Timer.objects.create(
            user=owner, child=self.child, start=self.start
        )

    def test_caregiver_cannot_consume_own_or_other_timer(self):
        self.assertFalse(self.user.has_perm("core.delete_timer"))
        for path, model in self.timer_entries:
            for owner in (self.user, self.other):
                with self.subTest(entry=path, owner=owner.username):
                    timer = self.timer(owner)
                    count = model.objects.count()
                    response = self.client.post(
                        f"/{path}/add/?timer={timer.pk}", self.entry_data(path)
                    )
                    self.assertTrue(models.Timer.objects.filter(pk=timer.pk).exists())
                    self.assertEqual(model.objects.count(), count)
                    self.assertIn(response.status_code, (200, 400, 403))

    def test_delete_timer_grant_allows_own_and_other_timer(self):
        self.grant("delete_timer")
        for path, model in self.timer_entries:
            for owner in (self.user, self.other):
                with self.subTest(entry=path, owner=owner.username):
                    timer = self.timer(owner)
                    count = model.objects.count()
                    response = self.client.post(
                        f"/{path}/add/?timer={timer.pk}", self.entry_data(path)
                    )
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(model.objects.count(), count + 1)
                    self.assertFalse(models.Timer.objects.filter(pk=timer.pk).exists())

    def test_invalid_timer_queries_do_not_crash_or_save(self):
        self.grant("delete_timer")
        for path, model in self.timer_entries:
            for timer_id in ("not-an-id", "-1", "999999999999999999999999999999"):
                with self.subTest(entry=path, timer=timer_id):
                    url = f"/{path}/add/?timer={timer_id}"
                    self.assertLess(self.client.get(url).status_code, 500)
                    count = model.objects.count()
                    response = self.client.post(url, self.entry_data(path))
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context["form"].errors)
                    self.assertEqual(model.objects.count(), count)

    def test_timer_deleted_between_get_and_post_does_not_save(self):
        self.grant("delete_timer")
        for path, model in self.timer_entries:
            with self.subTest(entry=path):
                timer = self.timer(self.other)
                url = f"/{path}/add/?timer={timer.pk}"
                self.assertEqual(self.client.get(url).status_code, 200)
                timer.delete()
                count = model.objects.count()
                response = self.client.post(url, self.entry_data(path))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.assertEqual(model.objects.count(), count)

    def test_validation_failure_retains_timer(self):
        self.grant("delete_timer")
        for path, model in self.timer_entries:
            with self.subTest(entry=path):
                timer = self.timer(self.other)
                count = model.objects.count()
                data = self.entry_data(path)
                data["end"] = (self.start - timezone.timedelta(minutes=1)).isoformat()
                response = self.client.post(f"/{path}/add/?timer={timer.pk}", data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].non_field_errors())
                self.assertTrue(models.Timer.objects.filter(pk=timer.pk).exists())
                self.assertEqual(model.objects.count(), count)

    def test_deferred_save_does_not_consume_timer_or_save_entry(self):
        self.grant("delete_timer")
        timer = self.timer(self.other)
        form = forms.SleepForm(
            data=self.entry_data("sleep"), user=self.user, timer=timer.pk
        )
        self.assertTrue(form.is_valid(), form.errors)
        count = models.Sleep.objects.count()
        instance = form.save(commit=False)
        self.assertIsNone(instance.pk)
        self.assertEqual(models.Sleep.objects.count(), count)
        self.assertTrue(models.Timer.objects.filter(pk=timer.pk).exists())

    def test_failed_save_rolls_back_entry_and_preserves_timer(self):
        self.grant("delete_timer")
        timer = self.timer(self.other)
        form = forms.SleepForm(
            data=self.entry_data("sleep"), user=self.user, timer=timer.pk
        )
        self.assertTrue(form.is_valid(), form.errors)
        count = models.Sleep.objects.count()
        real_save = form.instance.save

        def fail_after_save(*args, **kwargs):
            real_save(*args, **kwargs)
            raise RuntimeError("simulated write failure")

        with patch.object(form.instance, "save", side_effect=fail_after_save):
            with self.assertRaisesMessage(RuntimeError, "simulated write failure"):
                form.save()
        self.assertEqual(models.Sleep.objects.count(), count)
        self.assertTrue(models.Timer.objects.filter(pk=timer.pk).exists())

    def assert_tag_denied(self, response):
        self.assertIn(response.status_code, (200, 403))
        if response.status_code == 200:
            self.assertIn("tags", response.context["form"].errors)

    def note(self):
        note = models.Note.objects.create(
            child=self.child, note="Original", time=self.start
        )
        note.tags.add("first", "second")
        return note

    def note_data(self, **extra):
        return {
            "child": self.child.pk,
            "time": self.start.isoformat(),
            "note": "Updated",
            **extra,
        }

    def test_no_tag_permissions_cannot_create_or_assign_on_add(self):
        models.Tag.objects.create(name="existing")
        self.assertFalse(self.user.has_perm("core.add_tag"))
        self.assertFalse(self.user.has_perm("core.change_tag"))
        for tags in ("existing", "brand-new"):
            with self.subTest(tags=tags):
                count = models.Note.objects.count()
                tag_count = models.Tag.objects.count()
                response = self.client.post("/notes/add/", self.note_data(tags=tags))
                self.assert_tag_denied(response)
                self.assertEqual(models.Note.objects.count(), count)
                self.assertEqual(models.Tag.objects.count(), tag_count)

    def test_no_tag_permissions_cannot_assign_create_or_remove_on_edit(self):
        note = self.note()
        models.Tag.objects.create(name="existing")
        for tags in ("first,second,existing", "first,second,brand-new", "first", ""):
            with self.subTest(tags=tags):
                response = self.client.post(
                    f"/notes/{note.pk}/", self.note_data(tags=tags)
                )
                self.assert_tag_denied(response)
                note.refresh_from_db()
                self.assertEqual(note.note, "Original")
                self.assertSetEqual(set(note.tags.names()), {"first", "second"})
                self.assertFalse(models.Tag.objects.filter(name="brand-new").exists())

    def test_omitted_tags_preserve_edit_with_or_without_permission(self):
        note = self.note()
        for permitted in (False, True):
            with self.subTest(change_tag=permitted):
                if permitted:
                    self.grant("change_tag")
                response = self.client.post(f"/notes/{note.pk}/", self.note_data())
                self.assertEqual(response.status_code, 302)
                note.refresh_from_db()
                self.assertEqual(note.note, "Updated")
                self.assertSetEqual(set(note.tags.names()), {"first", "second"})

    def test_unchanged_tag_set_is_allowed_without_permissions(self):
        note = self.note()
        response = self.client.post(
            f"/notes/{note.pk}/", self.note_data(tags="second,first,first")
        )
        self.assertEqual(response.status_code, 302)
        note.refresh_from_db()
        self.assertEqual(note.note, "Updated")
        self.assertSetEqual(set(note.tags.names()), {"first", "second"})

    def test_change_tag_allows_existing_associations_and_removal(self):
        self.grant("change_tag")
        models.Tag.objects.create(name="existing")
        response = self.client.post("/notes/add/", self.note_data(tags="existing"))
        self.assertEqual(response.status_code, 302)
        note = models.Note.objects.latest("pk")
        self.assertSetEqual(set(note.tags.names()), {"existing"})
        for tags, expected in (
            ("existing,another", {"existing", "another"}),
            ("", set()),
        ):
            with self.subTest(tags=tags):
                models.Tag.objects.get_or_create(name="another")
                response = self.client.post(
                    f"/notes/{note.pk}/", self.note_data(tags=tags)
                )
                self.assertEqual(response.status_code, 302)
                self.assertSetEqual(set(note.tags.names()), expected)

    def test_change_tag_alone_cannot_create_new_tags(self):
        self.grant("change_tag")
        note = self.note()
        for url in ("/notes/add/", f"/notes/{note.pk}/"):
            with self.subTest(url=url):
                count = models.Note.objects.count()
                response = self.client.post(url, self.note_data(tags="brand-new"))
                self.assert_tag_denied(response)
                self.assertEqual(models.Note.objects.count(), count)
                self.assertFalse(models.Tag.objects.filter(name="brand-new").exists())
                self.assertSetEqual(set(note.tags.names()), {"first", "second"})

    def test_add_tag_alone_does_not_allow_association_changes(self):
        self.grant("add_tag")
        count = models.Note.objects.count()
        response = self.client.post("/notes/add/", self.note_data(tags="brand-new"))
        self.assert_tag_denied(response)
        self.assertEqual(models.Note.objects.count(), count)
        self.assertFalse(models.Tag.objects.filter(name="brand-new").exists())

    def test_add_and_change_tag_grants_allow_new_tags_on_add_and_edit(self):
        self.grant("add_tag", "change_tag")
        response = self.client.post("/notes/add/", self.note_data(tags="new-on-add"))
        self.assertEqual(response.status_code, 302)
        note = models.Note.objects.latest("pk")
        self.assertSetEqual(set(note.tags.names()), {"new-on-add"})
        response = self.client.post(
            f"/notes/{note.pk}/", self.note_data(tags="new-on-add,new-on-edit")
        )
        self.assertEqual(response.status_code, 302)
        self.assertSetEqual(set(note.tags.names()), {"new-on-add", "new-on-edit"})

    def test_unauthorized_tag_editor_is_hidden_but_fieldsets_still_hydrate(self):
        for path, model in self.timer_entries:
            entry = model.objects.create(
                **{
                    **self.entry_data(path),
                    "child": self.child,
                    "start": self.start,
                    "end": self.end,
                }
            )
            for url in (f"/{path}/add/", f"/{path}/{entry.pk}/"):
                with self.subTest(url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    form = response.context["form"]
                    self.assertEqual(form.user.pk, self.user.pk)
                    self.assertIn("tags", form.fields)
                    self.assertTrue(form["tags"].is_hidden)
                    self.assertIn(
                        "tags",
                        [
                            field.name
                            for group in form.hydrated_fielsets
                            for field in group["fields"]
                        ],
                    )

    def test_unauthorized_tag_field_posts_the_rendered_value_back_on_edit(self):
        note = self.note()
        response = self.client.get(f"/notes/{note.pk}/")
        rendered = response.context["form"]["tags"].value()
        if isinstance(rendered, list):
            rendered = ",".join(t.name for t in rendered)

        # Browsers resubmit exactly what the widget rendered.
        response = self.client.post(
            f"/notes/{note.pk}/", self.note_data(tags=rendered, note="Corrected")
        )
        self.assertEqual(response.status_code, 302)
        note.refresh_from_db()
        self.assertEqual(note.note, "Corrected")
        self.assertSetEqual(set(note.tags.names()), {"first", "second"})

        # A real tag change is still refused without tag permissions.
        response = self.client.post(
            f"/notes/{note.pk}/", self.note_data(tags="first,second,smuggled")
        )
        self.assert_tag_denied(response)
        note.refresh_from_db()
        self.assertEqual(note.note, "Corrected")
        self.assertSetEqual(set(note.tags.names()), {"first", "second"})
        self.assertFalse(models.Tag.objects.filter(name="smuggled").exists())

    def test_unauthorized_tag_edit_renders_tag_names_not_object_repr(self):
        note = self.note()
        response = self.client.get(f"/notes/{note.pk}/")
        rendered = response.context["form"]["tags"].value()
        html = response.content.decode()
        self.assertNotIn("<Tag:", html)
        names = sorted(t.name for t in rendered) if rendered else []
        self.assertEqual(names, ["first", "second"])

    def test_child_and_timer_add_edit_smoke(self):
        self.grant("add_child", "change_child")
        child_data = {
            "first_name": "New",
            "last_name": "Child",
            "birth_date": "2020-01-01",
        }
        self.assertEqual(self.client.get("/children/add/").status_code, 200)
        self.assertEqual(
            self.client.post("/children/add/", child_data).status_code, 302
        )
        child = models.Child.objects.get(first_name="New")
        child_url = f"/children/{child.slug}/edit/"
        self.assertEqual(self.client.get(child_url).status_code, 200)
        child_data["first_name"] = "Edited"
        self.assertEqual(self.client.post(child_url, child_data).status_code, 302)
        child.refresh_from_db()
        self.assertEqual(child.first_name, "Edited")
        data = {"child": child.pk, "name": "New timer", "start": self.start.isoformat()}
        self.assertEqual(self.client.get("/timers/add/").status_code, 200)
        self.assertEqual(self.client.post("/timers/add/", data).status_code, 302)
        timer = models.Timer.objects.get(name="New timer")
        self.assertEqual(timer.user_id, self.user.pk)
        url = f"/timers/{timer.pk}/edit/"
        self.assertEqual(self.client.get(url).status_code, 200)
        data["name"] = "Edited timer"
        self.assertEqual(self.client.post(url, data).status_code, 302)
        timer.refresh_from_db()
        self.assertEqual(timer.name, "Edited timer")
        self.assertEqual(timer.user_id, self.user.pk)
