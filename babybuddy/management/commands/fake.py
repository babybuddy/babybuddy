# -*- coding: utf-8 -*-
from random import choice, choices, randint, uniform
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand
from django.utils import timezone

from faker import Faker

from core import models


class Command(BaseCommand):
    help = "Generates fake children and related entries."

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.faker = Faker()
        self.child = None
        self.weight = None
        self.tags = []
        self.time = None
        self.time_now = timezone.localtime()

    def add_arguments(self, parser):
        parser.add_argument(
            "--children",
            dest="children",
            default=1,
            help="The number of fake children to create.",
        )
        parser.add_argument(
            "--days",
            dest="days",
            default=31,
            help="How many days of fake entries to create.",
        )

    def handle(self, *args, **kwargs):
        verbosity = int(kwargs["verbosity"])
        children = int(kwargs["children"]) or 1
        days = int(kwargs["days"]) or 31

        for i in range(0, 10):
            text = self.faker.password(randint(4, 10))
            try:
                tag = models.Tag.objects.create(name=text)
                tag.save()
                self.tags.append(tag)
            except IntegrityError:
                pass

        birth_date = timezone.localtime() - timedelta(days=days)
        for i in range(0, children):
            self.child = models.Child.objects.create(
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                birth_date=birth_date,
            )
            self.child.save()
            self._add_child_data()

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS("Successfully added fake data."))

    @transaction.atomic
    def _add_child_data(self):
        """
        Adds fake data for child from child.birth_date to now. The fake data
        follows a semi-regular pattern of sleep, feed, change, tummy time,
        change, tummy time, sleep, etc.
        :returns:
        """
        self.time = self.child.birth_date

        self.pumping = round(uniform(95.0, 102.0), 2)
        self._add_pumping_entry()

        self.temperature = round(uniform(95.0, 102.0), 2)
        self._add_temperature_entry()

        self.weight = round(uniform(8.0, 12.0), 2)
        self._add_weight_entry()
        last_weight_entry_time = self.time

        self.height = round(uniform(45.0, 60.0), 2)
        self._add_height_entry()
        last_height_entry_time = self.time

        self.head_circumference = round(uniform(8.0, 12.0), 2)
        self._add_head_circumference_entry()
        last_head_circumference_entry_time = self.time

        self.bmi = round(uniform(8.0, 12.0), 2)
        self._add_bmi_entry()
        last_bmi_entry_time = self.time

        self._add_note_entry()
        last_note_entry_time = self.time

        while self.time < self.time_now:
            self._add_sleep_entry()
            if choice([True, False]):
                self._add_diaperchange_entry()
            self._add_feeding_entry()
            self._add_diaperchange_entry()
            self._add_pumping_entry()
            if choice([True, False]):
                self._add_tummytime_entry()
            if choice([True, False]):
                self._add_diaperchange_entry()
                self._add_tummytime_entry()
            if choice([True, False]):
                self._add_temperature_entry()
            if choice([True, False]):
                self._add_pumping_entry()
            if (self.time - last_note_entry_time).days > 1 and choice([True, False]):
                self._add_note_entry()
                last_note_entry_time = self.time
            if (self.time - last_weight_entry_time).days > 6:
                self._add_weight_entry()
                last_weight_entry_time = self.time
            if (self.time - last_height_entry_time).days > 6:
                self._add_height_entry()
                last_height_entry_time = self.time
            if (self.time - last_head_circumference_entry_time).days > 6:
                self._add_head_circumference_entry()
                last_head_circumference_entry_time = self.time
            if (self.time - last_bmi_entry_time).days > 6:
                self._add_bmi_entry()
                last_bmi_entry_time = self.time

    @transaction.atomic
    def _add_pumping_entry(self):
        """
        Add a Pumping entry. This assumes a weekly interval.
        :returns:
        """
        self.amount = round(uniform(95.0, 102.0), 2)

        notes = ""
        if choice([True, False, False, False]):
            notes = " ".join(self.faker.sentences(randint(1, 5)))

        start = self.time + timedelta(minutes=randint(1, 60))
        end = start + timedelta(minutes=randint(5, 20))

        if end < self.time_now:
            models.Pumping.objects.create(
                child=self.child, amount=self.amount, start=start, end=end, notes=notes
            ).save()

    @transaction.atomic
    def _add_diaperchange_entry(self):
        """
        Add a Diaper Change entry and advance self.time.
        :returns:
        """
        solid = choice([True, False, False, False])
        wet = choice([True, False])
        color = ""
        if solid:
            color = choice(models.DiaperChange._meta.get_field("color").choices)[0]
        amount = Decimal("%d.%d" % (randint(0, 6), randint(1, 9)))
        time = self.time + timedelta(minutes=randint(1, 60))

        notes = ""
        if choice([True, False, False, False]):
            notes = " ".join(self.faker.sentences(randint(1, 5)))

        if time < self.time_now:
            instance = models.DiaperChange.objects.create(
                child=self.child,
                time=time,
                wet=wet,
                solid=solid,
                color=color,
                amount=amount,
                notes=notes,
            )
            instance.save()
            self._add_tags(instance)
        self.time = time

    @transaction.atomic
    def _add_feeding_entry(self):
        """
        Add a Feeding entry and advance self.time.
        :returns:
        """
        method = choice(models.Feeding._meta.get_field("method").choices)[0]
        amount = None
        if method == "bottle":
            amount = Decimal("%d.%d" % (randint(0, 6), randint(0, 9)))
        start = self.time + timedelta(minutes=randint(1, 60))
        end = start + timedelta(minutes=randint(5, 20))

        notes = ""
        if choice([True, False, False, False]):
            notes = " ".join(self.faker.sentences(randint(1, 5)))

        if end < self.time_now:
            instance = models.Feeding.objects.create(
                child=self.child,
                start=start,
                end=end,
                type=choice(models.Feeding._meta.get_field("type").choices)[0],
                method=method,
                amount=amount,
                notes=notes,
            )
            instance.save()
            self._add_tags(instance)
        self.time = end

    @transaction.atomic
    def _add_note_entry(self):
        """
        Add a Note entry.
        :returns:
        """
        note = self.faker.sentence()
        instance = models.Note.objects.create(child=self.child, note=note)
        instance.save()
        self._add_tags(instance)

    @transaction.atomic
    def _add_sleep_entry(self):
        """
        Add a Sleep entry and advance self.time. Between the hours of 18 and 6,
        extend the minimum and maximum sleep duration settings.
        :returns:
        """
        if self.time.hour < 6 or self.time.hour > 18:
            minutes = randint(60 * 2, 60 * 6)
        else:
            minutes = randint(30, 60 * 2)
        end = self.time + timedelta(minutes=minutes)

        notes = ""
        if choice([True, False, False, False]):
            notes = " ".join(self.faker.sentences(randint(1, 5)))

        if end < self.time_now:
            instance = models.Sleep.objects.create(
                child=self.child, start=self.time, end=end, notes=notes
            )
            instance.save()
            self._add_tags(instance)
        self.time = end

    @transaction.atomic
    def _add_temperature_entry(self):
        """
        Add a Temperature entry. This assumes a weekly interval.
        :returns:
        """
        self.temperature = round(uniform(95.0, 102.0), 2)

        notes = ""
        if choice([True, False, False, False]):
            notes = " ".join(self.faker.sentences(randint(1, 5)))

        instance = models.Temperature.objects.create(
            child=self.child, temperature=self.temperature, time=self.time, notes=notes
        )
        instance.save()
        self._add_tags(instance)

    @transaction.atomic
    def _add_tummytime_entry(self):
        """
        Add a Tummy time entry and advance self.time.
        :returns:
        """
        milestone = ""
        if choice([True, False]):
            milestone = self.faker.sentence()
        start = self.time + timedelta(minutes=randint(1, 60))
        end = start + timedelta(minutes=randint(0, 10), seconds=randint(0, 59))
        if (end - start).seconds < 20:
            end = start + timedelta(minutes=1, seconds=30)

        if end < self.time_now:
            instance = models.TummyTime.objects.create(
                child=self.child, start=start, end=end, milestone=milestone
            )
            instance.save()
            self._add_tags(instance)
        self.time = end

    @transaction.atomic
    def _add_weight_entry(self):
        """
        Add a Weight entry. This assumes a weekly interval.
        :returns:
        """
        self.weight += uniform(0.1, 0.3)

        notes = ""
        if choice([True, False, False, False]):
            notes = " ".join(self.faker.sentences(randint(1, 5)))

        instance = models.Weight.objects.create(
            child=self.child,
            weight=round(self.weight, 2),
            date=self.time.date(),
            notes=notes,
        )
        instance.save()
        self._add_tags(instance)

    @transaction.atomic
    def _add_height_entry(self):
        """
        Add a height entry. This assumes a weekly interval.
        :returns:
        """
        self.height += uniform(0.1, 0.3)

        notes = ""
        if choice([True, False, False, False]):
            notes = " ".join(self.faker.sentences(randint(1, 5)))

        instance = models.Height.objects.create(
            child=self.child,
            height=round(self.height, 2),
            date=self.time.date(),
            notes=notes,
        )
        instance.save()
        self._add_tags(instance)

    @transaction.atomic
    def _add_head_circumference_entry(self):
        """
        Add a head circumference entry. This assumes a weekly interval.
        :returns:
        """
        self.head_circumference += uniform(0.1, 0.3)

        notes = ""
        if choice([True, False, False, False]):
            notes = " ".join(self.faker.sentences(randint(1, 5)))

        instance = models.HeadCircumference.objects.create(
            child=self.child,
            head_circumference=round(self.head_circumference, 2),
            date=self.time.date(),
            notes=notes,
        )
        instance.save()
        self._add_tags(instance)

    @transaction.atomic
    def _add_bmi_entry(self):
        """
        Add a BMI entry. This assumes a weekly interval.
        :returns:
        """
        self.bmi += uniform(0.1, 0.3)

        notes = ""
        if choice([True, False, False, False]):
            notes = " ".join(self.faker.sentences(randint(1, 5)))

        instance = models.BMI.objects.create(
            child=self.child, bmi=round(self.bmi, 2), date=self.time.date(), notes=notes
        )
        instance.save()
        self._add_tags(instance)

    @transaction.atomic
    def _add_tags(self, instance):
        if choice([True, False, False, False]):
            instance.tags.add(*choices(self.tags, k=randint(1, 5)))
