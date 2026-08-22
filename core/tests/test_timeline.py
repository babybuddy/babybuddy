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
                instance = model.objects.create(
                    child=self.child, start=start_time, end=end_time
                )

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
