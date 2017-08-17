# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from core.models import (Child, DiaperChange, Feeding, Note, Sleep, Timer,
                         TummyTime)


class ChildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Child
        fields = ('first_name', 'last_name', 'birth_date')


class DiaperChangeSerializer(serializers.HyperlinkedModelSerializer):
    child = serializers.HyperlinkedIdentityField(view_name='api:child-detail')

    class Meta:
        model = DiaperChange
        fields = ('child', 'time', 'wet', 'solid', 'color')


class FeedingSerializer(serializers.HyperlinkedModelSerializer):
    child = serializers.HyperlinkedIdentityField(view_name='api:child-detail')

    class Meta:
        model = Feeding
        fields = ('child', 'start', 'end', 'duration', 'type', 'method',
                  'amount')


class NoteSerializer(serializers.HyperlinkedModelSerializer):
    child = serializers.HyperlinkedIdentityField(view_name='api:child-detail')

    class Meta:
        model = Note
        fields = ('child', 'note', 'time')


class SleepSerializer(serializers.HyperlinkedModelSerializer):
    child = serializers.HyperlinkedIdentityField(view_name='api:child-detail')

    class Meta:
        model = Sleep
        fields = ('child', 'start', 'end', 'duration')


class TimerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Timer
        fields = ('name', 'start', 'end', 'duration', 'active')


class TummyTimeSerializer(serializers.HyperlinkedModelSerializer):
    child = serializers.HyperlinkedIdentityField(view_name='api:child-detail')

    class Meta:
        model = TummyTime
        fields = ('child', 'start', 'end', 'duration', 'milestone')
