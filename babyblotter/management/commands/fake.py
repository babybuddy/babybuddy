# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from random import randint, choice
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from faker import Factory

from core.models import Child, DiaperChange, Feeding, Sleep, TummyTime


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

    def handle(self, *args, **kwargs):
        verbosity = kwargs['verbosity'] or 1
        children = kwargs['children'] or 1

        for i in range(0, children):
            child = Child.objects.create(
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                birth_date=self.faker.date()
            )
            child.save()

            for j in range(1, 6):
                date = timezone.now() - timedelta(days=j)
                self._add_child_data(child, date)

        if verbosity > 0:
            self.stdout.write(
                self.style.SUCCESS('Successfully added fake data.')
            )

    def _add_child_data(self, child, date):
        for i in (range(0, randint(5, 20))):
            solid = choice([True, False])
            if solid:
                wet = False
                color = choice(
                    DiaperChange._meta.get_field('color').choices)[0]
            else:
                wet = True
                color = ''

            DiaperChange.objects.create(
                child=child,
                time=date + timedelta(seconds=randint(-86400, 86400)),
                wet=wet,
                solid=solid,
                color=color
            ).save()

        for i in (range(0, randint(5, 20))):
            start = date + timedelta(seconds=randint(-86400, 86400))
            method = choice(Feeding._meta.get_field('method').choices)[0]

            if method is 'bottle':
                amount = Decimal('%d.%d' % (randint(0, 6), randint(0, 9)))
            else:
                amount = None

            Feeding.objects.create(
                child=child,
                start=start,
                end=start + timedelta(minutes=randint(5, 60)),
                type=choice(Feeding._meta.get_field('type').choices)[0],
                method=method,
                amount=amount
            ).save()

        for i in (range(0, randint(2, 10))):
            start = date + timedelta(seconds=randint(-86400, 86400))

            Sleep.objects.create(
                child=child,
                start=start,
                end=start + timedelta(minutes=randint(5, 120))
            ).save()

        for i in (range(0, randint(2, 10))):
            start = date + timedelta(seconds=randint(-86400, 86400))

            if choice([True, False]):
                milestone = self.faker.sentence()
            else:
                milestone = ''

            TummyTime.objects.create(
                child=child,
                start=start,
                end=start + timedelta(minutes=randint(1, 10)),
                milestone=milestone
            ).save()


