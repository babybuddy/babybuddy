import datetime
from django.test import TestCase
from django.utils import timezone
from core import models
from core.timeline import get_objects


class TimelineTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.child = models.Child.objects.create(
            first_name="Test", last_name="Child", birth_date=timezone.now().date()
        )

    def test_cross_midnight_events(self):
        """
        Events that span across midnight should split their start and end
        dictionaries accurately across the two respective days.
        """
        day_1 = timezone.make_aware(datetime.datetime(2023, 1, 1))
        day_2 = timezone.make_aware(datetime.datetime(2023, 1, 2))

        start_time = day_1.replace(hour=23, minute=0)
        end_time = day_2.replace(hour=1, minute=0)

        models_to_test = [
            models.Sleep,
            models.TummyTime,
            models.Feeding,
        ]

        for model in models_to_test:
            with self.subTest(model=model.__name__):
                create_kwargs = {
                    "child": self.child,
                    "start": start_time,
                    "end": end_time,
                }
                if model is models.Feeding:
                    create_kwargs.update(type="formula", method="bottle")
                instance = model.objects.create(**create_kwargs)

                events_day_1 = get_objects(date=day_1, child=self.child)
                events_day_2 = get_objects(date=day_2, child=self.child)

                # Day 1: should only contain the "start" event
                self.assertEqual(len(events_day_1), 1)
                self.assertEqual(events_day_1[0]["type"], "start")
                self.assertEqual(events_day_1[0]["time"], start_time)

                # Day 2: should only contain the "end" event
                self.assertEqual(len(events_day_2), 1)
                self.assertEqual(events_day_2[0]["type"], "end")
                self.assertEqual(events_day_2[0]["time"], end_time)

                instance.delete()

    def test_tummy_time_notes_appear_in_timeline(self):
        """
        Notes on a Tummy Time entry should reach the timeline events, like the
        notes of the other care entry models do.
        """
        day = timezone.make_aware(datetime.datetime(2023, 1, 1))
        start = day.replace(hour=10, minute=0)
        end = day.replace(hour=10, minute=10)

        models.TummyTime.objects.create(
            child=self.child,
            start=start,
            end=end,
            milestone="Lifted head",
            notes="Seemed tired today",
        )

        events = get_objects(date=day, child=self.child)

        self.assertEqual(len(events), 2)
        for event in events:
            self.assertIn("Lifted head", event["details"])
            self.assertIn("Seemed tired today", event["details"])

    def test_medication_next_dose_spanning_midnight(self):
        """
        Medication doses with a next_dose_interval that wear off on the next day
        should show the start on Day 1 and the end ("wore off") on Day 2.
        """
        day_1 = timezone.make_aware(datetime.datetime(2023, 1, 1))
        day_2 = timezone.make_aware(datetime.datetime(2023, 1, 2))

        start_time = day_1.replace(hour=23, minute=0)
        interval = datetime.timedelta(hours=2)

        instance = models.Medication.objects.create(
            child=self.child,
            name="Tylenol",
            time=start_time,
            next_dose_interval=interval,
        )

        events_day_1 = get_objects(date=day_1, child=self.child)
        events_day_2 = get_objects(date=day_2, child=self.child)

        # Day 1: should contain the "start" event
        self.assertEqual(len(events_day_1), 1)
        self.assertEqual(events_day_1[0]["type"], "start")
        self.assertEqual(events_day_1[0]["time"], start_time)

        # Day 2: should contain the "end" event (wore off)
        self.assertEqual(len(events_day_2), 1)
        self.assertEqual(events_day_2[0]["type"], "end")
        self.assertEqual(events_day_2[0]["time"], start_time + interval)

        instance.delete()
