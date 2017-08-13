# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from core.models import Baby, DiaperChange, Feeding, Sleep, TummyTime


class BabySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Baby
        fields = ('first_name', 'last_name', 'birth_date')


class DiaperChangeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DiaperChange
        fields = ('baby', 'time', 'wet', 'solid', 'color')


class FeedingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Feeding
        fields = ('baby', 'start', 'end', 'duration', 'type', 'method')


class SleepSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sleep
        fields = ('baby', 'start', 'end', 'duration')


class TummyTimeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TummyTime
        fields = ('baby', 'start', 'end', 'duration', 'milestone')
