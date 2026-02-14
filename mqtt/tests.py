# -*- coding: utf-8 -*-
"""Tests for the mqtt app.

All tests mock the paho-mqtt client so no real broker is needed.
Run with:
    DJANGO_SETTINGS_MODULE=babybuddy.settings.test pipenv run python manage.py test mqtt
"""

import datetime
import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.models import (
    BMI,
    Child,
    DiaperChange,
    Feeding,
    Medication,
    MedicationSchedule,
    Sleep,
    Temperature,
    Timer,
    Weight,
)

from mqtt.client import MqttClient
from mqtt.discovery import (
    DISCOVERY_ENTITIES,
    publish_all_discovery,
    publish_child_discovery,
    remove_child_discovery,
)
from mqtt.publisher import (
    on_model_delete,
    on_model_save,
    publish_all_state,
)
from mqtt.serializers import (
    MqttChildSerializer,
    MqttDiaperChangeSerializer,
    MqttFeedingSerializer,
    MqttTimerSerializer,
)
from mqtt.stats import compute_stats


def _create_child(first_name="Leo", last_name="Test"):
    """Helper: create and return a Child instance."""
    return Child.objects.create(
        first_name=first_name,
        last_name=last_name,
        birth_date=datetime.date(2024, 1, 15),
    )


def _mock_mqtt_settings(enabled=True, topic_prefix="babybuddy"):
    """Return a MagicMock that behaves like the MqttSettings dbsettings group."""
    s = MagicMock()
    s.enabled = enabled
    s.topic_prefix = topic_prefix
    s.broker_host = "localhost"
    s.broker_port = 1883
    s.username = ""
    s.password = ""
    s.use_tls = False
    return s


# -----------------------------------------------------------------------
# Test serializers (no request context needed)
# -----------------------------------------------------------------------


class MqttSerializerTests(TestCase):
    def setUp(self):
        self.child = _create_child()

    def test_feeding_serializer_produces_valid_json(self):
        now = timezone.now()
        feeding = Feeding.objects.create(
            child=self.child,
            start=now - datetime.timedelta(minutes=30),
            end=now,
            type="breast milk",
            method="both breasts",
            amount=120,
        )
        data = MqttFeedingSerializer(feeding).data
        # Should be JSON-encodable without errors
        raw = json.dumps(data, default=str)
        parsed = json.loads(raw)
        self.assertEqual(parsed["id"], feeding.id)
        self.assertEqual(parsed["child"], self.child.id)
        self.assertEqual(parsed["child_name"], "Leo Test")
        self.assertEqual(parsed["child_slug"], self.child.slug)
        self.assertNotIn("url", parsed)  # No hyperlinked URL

    def test_child_serializer(self):
        data = MqttChildSerializer(self.child).data
        raw = json.dumps(data, default=str)
        parsed = json.loads(raw)
        self.assertEqual(parsed["first_name"], "Leo")
        self.assertEqual(parsed["slug"], self.child.slug)
        self.assertNotIn("url", parsed)

    def test_diaper_change_serializer(self):
        dc = DiaperChange.objects.create(
            child=self.child, time=timezone.now(), wet=True, solid=False
        )
        data = MqttDiaperChangeSerializer(dc).data
        raw = json.dumps(data, default=str)
        parsed = json.loads(raw)
        self.assertEqual(parsed["child_slug"], self.child.slug)
        self.assertTrue(parsed["wet"])

    def test_timer_serializer_no_child(self):
        """Timer can have child=None."""
        user = get_user_model().objects.create_user("testuser", password="pass")
        timer = Timer.objects.create(
            name="Test Timer",
            start=timezone.now(),
            user=user,
            child=None,
        )
        data = MqttTimerSerializer(timer).data
        raw = json.dumps(data, default=str)
        parsed = json.loads(raw)
        self.assertIsNone(parsed["child"])
        self.assertIsNone(parsed["child_name"])
        self.assertIsNone(parsed["child_slug"])


# -----------------------------------------------------------------------
# Test stats computation
# -----------------------------------------------------------------------


class ComputeStatsTests(TestCase):
    def setUp(self):
        self.child = _create_child()

    def test_empty_stats(self):
        stats = compute_stats(self.child)
        self.assertEqual(stats["feedings_today"], 0)
        self.assertEqual(stats["diaper_changes_today"], 0)
        self.assertEqual(stats["sleep_total_today_minutes"], 0)
        self.assertIsNone(stats["last_feeding_minutes_ago"])
        self.assertIsNone(stats["last_diaper_change_minutes_ago"])
        self.assertEqual(stats["medications_overdue"], [])
        self.assertEqual(stats["medications_overdue_count"], 0)

    def test_stats_with_data(self):
        now = timezone.now()

        # Create feedings today
        Feeding.objects.create(
            child=self.child,
            start=now - datetime.timedelta(hours=2),
            end=now - datetime.timedelta(hours=1, minutes=30),
            type="breast milk",
            method="both breasts",
        )
        Feeding.objects.create(
            child=self.child,
            start=now - datetime.timedelta(minutes=45),
            end=now - datetime.timedelta(minutes=15),
            type="formula",
            method="bottle",
        )

        # Diaper change
        DiaperChange.objects.create(
            child=self.child,
            time=now - datetime.timedelta(minutes=60),
            wet=True,
            solid=False,
        )

        stats = compute_stats(self.child)
        self.assertEqual(stats["feedings_today"], 2)
        self.assertEqual(stats["diaper_changes_today"], 1)
        self.assertIsNotNone(stats["last_feeding_minutes_ago"])
        self.assertIsNotNone(stats["last_diaper_change_minutes_ago"])

    def test_overdue_medication(self):
        schedule = MedicationSchedule.objects.create(
            child=self.child,
            name="Vitamin D",
            frequency="daily",
            schedule_time=datetime.time(8, 0),
            active=True,
        )
        # Create a dose from yesterday morning (early enough that the
        # 12-hour buffer in next_due_time doesn't push the next due to
        # tomorrow).
        yesterday_morning = timezone.now().replace(
            hour=7, minute=0, second=0, microsecond=0
        ) - datetime.timedelta(days=1)
        Medication.objects.create(
            child=self.child,
            medication_schedule=schedule,
            name="Vitamin D",
            time=yesterday_morning,
        )

        stats = compute_stats(self.child)
        # If it's past 08:00 today and no dose today, should be overdue
        now = timezone.localtime()
        if now.time() > datetime.time(8, 0):
            self.assertIn("Vitamin D", stats["medications_overdue"])
            self.assertGreaterEqual(stats["medications_overdue_count"], 1)


# -----------------------------------------------------------------------
# Test signal handlers / publisher (mocked MQTT client)
# -----------------------------------------------------------------------


class PublisherSignalTests(TestCase):
    def setUp(self):
        self.child = _create_child()

    @patch("mqtt.publisher.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.publisher.get_mqtt_settings")
    @patch("mqtt.publisher.mqtt_client")
    def test_feeding_save_publishes(
        self, mock_client, mock_get_settings, mock_get_prefix
    ):
        mock_client.is_started = True
        mock_get_settings.return_value = _mock_mqtt_settings(enabled=True)

        now = timezone.now()
        feeding = Feeding.objects.create(
            child=self.child,
            start=now - datetime.timedelta(minutes=30),
            end=now,
            type="breast milk",
            method="bottle",
        )
        on_model_save(Feeding, feeding, created=True)

        # Should have published to feeding/state and stats/state
        call_topics = [call[0][0] for call in mock_client.publish.call_args_list]
        self.assertIn(f"babybuddy/{self.child.slug}/feeding/state", call_topics)
        self.assertIn(f"babybuddy/{self.child.slug}/stats/state", call_topics)

        # Verify feeding payload
        for call in mock_client.publish.call_args_list:
            topic = call[0][0]
            if topic == f"babybuddy/{self.child.slug}/feeding/state":
                payload = json.loads(call[0][1])
                self.assertEqual(payload["id"], feeding.id)
                self.assertEqual(payload["child_slug"], self.child.slug)
                break

    @patch("mqtt.publisher.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.publisher.get_mqtt_settings")
    @patch("mqtt.publisher.mqtt_client")
    def test_diaper_change_save_publishes(
        self, mock_client, mock_get_settings, mock_get_prefix
    ):
        mock_client.is_started = True
        mock_get_settings.return_value = _mock_mqtt_settings(enabled=True)

        dc = DiaperChange.objects.create(
            child=self.child, time=timezone.now(), wet=True, solid=True, color="yellow"
        )
        on_model_save(DiaperChange, dc, created=True)

        call_topics = [call[0][0] for call in mock_client.publish.call_args_list]
        self.assertIn(f"babybuddy/{self.child.slug}/diaper_change/state", call_topics)

    @patch("mqtt.publisher.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.publisher.get_mqtt_settings")
    @patch("mqtt.publisher.mqtt_client")
    def test_delete_publishes_previous_entry(
        self, mock_client, mock_get_settings, mock_get_prefix
    ):
        mock_client.is_started = True
        mock_get_settings.return_value = _mock_mqtt_settings(enabled=True)

        now = timezone.now()
        temp1 = Temperature.objects.create(
            child=self.child, temperature=36.5, time=now - datetime.timedelta(hours=2)
        )
        temp2 = Temperature.objects.create(child=self.child, temperature=37.0, time=now)

        # Delete the latest
        temp2.delete()
        on_model_delete(Temperature, temp2)

        call_topics = [call[0][0] for call in mock_client.publish.call_args_list]
        self.assertIn(f"babybuddy/{self.child.slug}/temperature/state", call_topics)

        # The payload should now show temp1
        for call in mock_client.publish.call_args_list:
            topic = call[0][0]
            if topic == f"babybuddy/{self.child.slug}/temperature/state":
                payload = json.loads(call[0][1])
                self.assertEqual(payload["id"], temp1.id)
                break

    @patch("mqtt.publisher.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.publisher.get_mqtt_settings")
    @patch("mqtt.publisher.mqtt_client")
    def test_child_create_triggers_discovery(
        self, mock_client, mock_get_settings, mock_get_prefix
    ):
        mock_client.is_started = True
        mock_get_settings.return_value = _mock_mqtt_settings(enabled=True)

        new_child = Child.objects.create(
            first_name="Mia",
            last_name="Test",
            birth_date=datetime.date(2024, 6, 1),
        )
        with patch("mqtt.publisher.publish_child_discovery") as mock_disc:
            on_model_save(Child, new_child, created=True)
            mock_disc.assert_called_once_with(new_child)

    @patch("mqtt.publisher.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.publisher.get_mqtt_settings")
    @patch("mqtt.publisher.mqtt_client")
    def test_medication_schedule_publishes_list(
        self, mock_client, mock_get_settings, mock_get_prefix
    ):
        mock_client.is_started = True
        mock_get_settings.return_value = _mock_mqtt_settings(enabled=True)

        schedule = MedicationSchedule.objects.create(
            child=self.child,
            name="Vitamin D",
            frequency="daily",
            schedule_time=datetime.time(8, 0),
            active=True,
        )
        on_model_save(MedicationSchedule, schedule, created=True)

        # Should publish the full list to medication_schedule/state
        for call in mock_client.publish.call_args_list:
            topic = call[0][0]
            if topic == f"babybuddy/{self.child.slug}/medication_schedule/state":
                payload = json.loads(call[0][1])
                self.assertIsInstance(payload, list)
                self.assertEqual(len(payload), 1)
                self.assertEqual(payload[0]["name"], "Vitamin D")
                break
        else:
            self.fail("medication_schedule/state topic not published")

    @patch("mqtt.publisher.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.publisher.get_mqtt_settings")
    @patch("mqtt.publisher.mqtt_client")
    def test_disabled_setting_prevents_publish(
        self, mock_client, mock_get_settings, mock_get_prefix
    ):
        """When MQTT is disabled in site settings, signal handlers should not publish."""
        mock_client.is_started = False
        mock_get_settings.return_value = _mock_mqtt_settings(enabled=False)

        now = timezone.now()
        feeding = Feeding.objects.create(
            child=self.child,
            start=now - datetime.timedelta(minutes=30),
            end=now,
            type="breast milk",
            method="bottle",
        )
        on_model_save(Feeding, feeding, created=True)

        # No publish calls should have been made
        mock_client.publish.assert_not_called()

    @patch("mqtt.publisher.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.publisher.get_mqtt_settings")
    @patch("mqtt.publisher.mqtt_client")
    def test_enable_lazy_starts_client(
        self, mock_client, mock_get_settings, mock_get_prefix
    ):
        """When MQTT is enabled but client not started, it should lazy-start."""
        mock_client.is_started = False
        mock_get_settings.return_value = _mock_mqtt_settings(enabled=True)

        # After start() is called, is_started becomes True
        def start_side_effect():
            mock_client.is_started = True

        mock_client.start.side_effect = start_side_effect

        now = timezone.now()
        feeding = Feeding.objects.create(
            child=self.child,
            start=now - datetime.timedelta(minutes=30),
            end=now,
            type="breast milk",
            method="bottle",
        )
        on_model_save(Feeding, feeding, created=True)

        # Client should have been started
        mock_client.start.assert_called_once()
        # And publishing should proceed
        self.assertTrue(mock_client.publish.called)


# -----------------------------------------------------------------------
# Test discovery
# -----------------------------------------------------------------------


class DiscoveryTests(TestCase):
    def setUp(self):
        self.child = _create_child()

    @patch("mqtt.discovery.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.discovery.mqtt_client")
    def test_publish_child_discovery(self, mock_client, mock_get_prefix):
        publish_child_discovery(self.child)

        # Should have published one config per entity
        self.assertEqual(mock_client.publish.call_count, len(DISCOVERY_ENTITIES))

        # Verify structure of the first call
        first_call = mock_client.publish.call_args_list[0]
        topic = first_call[0][0]
        payload = json.loads(first_call[0][1])

        self.assertIn("homeassistant/", topic)
        self.assertIn("/config", topic)
        self.assertIn("unique_id", payload)
        self.assertIn("state_topic", payload)
        self.assertIn("device", payload)
        self.assertIn("availability_topic", payload)
        self.assertEqual(
            payload["device"]["identifiers"],
            [f"babybuddy_{self.child.slug}"],
        )

    @patch("mqtt.discovery.mqtt_client")
    def test_remove_child_discovery(self, mock_client):
        remove_child_discovery(self.child)

        self.assertEqual(mock_client.publish.call_count, len(DISCOVERY_ENTITIES))
        # All payloads should be empty strings (removes entity from HA)
        for call in mock_client.publish.call_args_list:
            payload = call[0][1]
            self.assertEqual(payload, "")

    @patch("mqtt.discovery.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.discovery.mqtt_client")
    def test_publish_all_discovery(self, mock_client, mock_get_prefix):
        _create_child("Mia", "Second")

        publish_all_discovery()

        # 2 children x N entities
        expected = Child.objects.count() * len(DISCOVERY_ENTITIES)
        self.assertEqual(mock_client.publish.call_count, expected)


# -----------------------------------------------------------------------
# Test publish_all_state
# -----------------------------------------------------------------------


class PublishAllStateTests(TestCase):
    def setUp(self):
        self.child = _create_child()

    @patch("mqtt.publisher.get_topic_prefix", return_value="babybuddy")
    @patch("mqtt.publisher.mqtt_client")
    def test_publish_all_state(self, mock_client, mock_get_prefix):
        publish_all_state()

        # Should have published child/state + one per model + medication_schedule + stats
        call_topics = [call[0][0] for call in mock_client.publish.call_args_list]
        slug = self.child.slug
        self.assertIn(f"babybuddy/{slug}/child/state", call_topics)
        self.assertIn(f"babybuddy/{slug}/feeding/state", call_topics)
        self.assertIn(f"babybuddy/{slug}/diaper_change/state", call_topics)
        self.assertIn(f"babybuddy/{slug}/sleep/state", call_topics)
        self.assertIn(f"babybuddy/{slug}/medication_schedule/state", call_topics)
        self.assertIn(f"babybuddy/{slug}/stats/state", call_topics)


# -----------------------------------------------------------------------
# Test MQTT disabled
# -----------------------------------------------------------------------


class MqttDisabledTests(TestCase):
    def test_client_does_not_start_when_not_called(self):
        client = MqttClient()
        # Client should not be started until explicitly started.
        self.assertFalse(client.is_started)
        self.assertFalse(client.is_connected())

    def test_publish_is_noop_when_not_started(self):
        client = MqttClient()
        # Should not raise
        client.publish("test/topic", "payload")
