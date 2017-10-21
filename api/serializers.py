# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from django.contrib.auth.models import User

from core.models import (Child, DiaperChange, Feeding, Note, Sleep, Timer,
                         TummyTime)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class ChildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Child
        fields = ('first_name', 'last_name', 'birth_date', 'slug')
        lookup_field = 'slug'


class DiaperChangeSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = DiaperChange
        fields = ('child', 'time', 'wet', 'solid', 'color')


class FeedingSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = Feeding
        fields = ('child', 'start', 'end', 'duration', 'type', 'method',
                  'amount')


class NoteSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = Note
        fields = ('child', 'note', 'time')


class SleepSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = Sleep
        fields = ('child', 'start', 'end', 'duration')


class TimerSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Timer
        fields = ('name', 'start', 'end', 'duration', 'active', 'user')


class TummyTimeSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = TummyTime
        fields = ('child', 'start', 'end', 'duration', 'milestone')
