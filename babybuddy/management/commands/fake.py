# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from random import randint, choice
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from faker import Factory

from core import models


class Command(BaseCommand):
    help = 'Generates fake children and related entries.'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.faker = Factory.create()

    def add_arguments(self, parser):
        parser.add_argument(
            '--children',
            dest='children',
            default=1,
            help='The number of fake children to create.'
        )
        parser.add_argument(
            '--days',
            dest='days',
            default=31,
            help='How many days of fake entries to create.'
        )

    def handle(self, *args, **kwargs):
        verbosity = int(kwargs['verbosity'])
        children = int(kwargs['children']) or 1
        days = int(kwargs['days']) or 31

        # User first day of data that will created for birth date.
        birth_date = (timezone.localtime() - timedelta(days=days))
        for i in range(0, children):
            child = models.Child.objects.create(
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                birth_date=birth_date
            )
            child.save()

            for j in range(days - 1, -1, -1):
                date = (timezone.localtime() - timedelta(days=j)).replace(
                    hour=0, minute=0, second=0)
                self._add_child_data(child, date)

        if verbosity > 0:
            self.stdout.write(
                self.style.SUCCESS('Successfully added fake data.')
            )

    def _add_child_data(self, child, date):
        now = timezone.localtime()

        for i in (range(0, randint(5, 20))):
            solid = choice([True, False])
            if solid:
                wet = False
                color = choice(
                    models.DiaperChange._meta.get_field('color').choices)[0]
            else:
                wet = True
                color = ''

            time = date + timedelta(minutes=randint(0, 60 * 24))

            if time < now:
                models.DiaperChange.objects.create(
                    child=child,
                    time=time,
                    wet=wet,
                    solid=solid,
                    color=color
                ).save()

        last_end = date
        while last_end < date + timedelta(days=1):
            method = choice(models.Feeding._meta.get_field(
                'method').choices)[0]
            if method is 'bottle':
                amount = Decimal('%d.%d' % (randint(0, 6), randint(0, 9)))
            else:
                amount = None

            start = last_end + timedelta(minutes=randint(0, 60 * 2))
            end = start + timedelta(minutes=randint(5, 20))
            if end > now:
                break

            models.Feeding.objects.create(
                child=child,
                start=start,
                end=end,
                type=choice(models.Feeding._meta.get_field('type').choices)[0],
                method=method,
                amount=amount
            ).save()
            last_end = end

        last_end = date

        # Adjust last_end if the last sleep entry crossed in to date.
        last_entry = models.Sleep.objects.filter(
            child=child).order_by('end').last()
        if last_entry:
            last_entry_end = timezone.localtime(last_entry.end)
            if last_entry_end > last_end:
                last_end = last_entry_end

        while last_end < date + timedelta(days=1):
            start = last_end + timedelta(minutes=randint(0, 60 * 2))
            if start.date() != date.date():
                break

            end = start + timedelta(minutes=randint(10, 60 * 3))
            if end > now:
                break

            models.Sleep.objects.create(
                child=child, start=start, end=end).save()
            last_end = end

        last_end = date
        while last_end < date + timedelta(days=1):
            if choice([True, False]):
                milestone = self.faker.sentence()
            else:
                milestone = ''

            start = last_end + timedelta(minutes=randint(0, 60 * 5))
            end = start + timedelta(minutes=randint(1, 10))
            if end > now:
                break

            models.TummyTime.objects.create(
                child=child,
                start=start,
                end=end,
                milestone=milestone
            ).save()
            last_end = end

        models.Weight.objects.create(
            child=child,
            weight=Decimal('%d.%d' % (randint(3, 15), randint(0, 9))),
            date=date.date()
        ).save()

        note = self.faker.sentence()
        models.Note.objects.create(
            child=child,
            note=note,
            time=date + timedelta(minutes=randint(0, 60 * 24))
        ).save()
