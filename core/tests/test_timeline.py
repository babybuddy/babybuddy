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

    def test_same_timestamp_end_before_instant_before_start(self):
        day = timezone.make_aware(datetime.datetime(2023, 1, 1))
        shared_time = day.replace(hour=11, minute=44, second=0)
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=day.replace(hour=11, minute=0),
            end=shared_time,
            type="formula",
            method="bottle",
        )
        diaper = models.DiaperChange.objects.create(
            child=self.child, time=shared_time, wet=True, solid=False
        )
        sleep = models.Sleep.objects.create(
            child=self.child,
            start=shared_time,
            end=day.replace(hour=12, minute=0),
        )
        events = get_objects(date=day, child=self.child)
        same_time_events = [e for e in events if e["time"] == shared_time]
        self.assertEqual(len(same_time_events), 3)
        self.assertEqual(same_time_events[0]["type"], "end")
        self.assertEqual(same_time_events[0]["model_name"], "feeding")
        self.assertIsNone(same_time_events[1].get("type"))
        self.assertEqual(same_time_events[1]["model_name"], "diaperchange")
        self.assertEqual(same_time_events[2]["type"], "start")
        self.assertEqual(same_time_events[2]["model_name"], "sleep")
        feeding.delete()
        diaper.delete()
        sleep.delete()
