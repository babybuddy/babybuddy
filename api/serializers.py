# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from core.models import Child, DiaperChange, Feeding, Note, Sleep, TummyTime


class ChildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Child
        fields = ('first_name', 'last_name', 'birth_date')


class DiaperChangeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DiaperChange
        fields = ('baby', 'time', 'wet', 'solid', 'color')


class FeedingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Feeding
        fields = ('baby', 'start', 'end', 'duration', 'type', 'method',
                  'amount')


class NoteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Note
        fields = ('baby', 'note', 'time')


class SleepSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sleep
        fields = ('baby', 'start', 'end', 'duration')


class TummyTimeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TummyTime
        fields = ('baby', 'start', 'end', 'duration', 'milestone')
