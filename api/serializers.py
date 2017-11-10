# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from django.contrib.auth.models import User

from core import models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class ChildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Child
        fields = ('first_name', 'last_name', 'birth_date', 'slug')
        lookup_field = 'slug'


class DiaperChangeSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = models.DiaperChange
        fields = ('child', 'time', 'wet', 'solid', 'color')


class FeedingSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = models.Feeding
        fields = ('child', 'start', 'end', 'duration', 'type', 'method',
                  'amount')


class NoteSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = models.Note
        fields = ('child', 'note', 'time')


class SleepSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = models.Sleep
        fields = ('child', 'start', 'end', 'duration')


class TimerSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()

    class Meta:
        model = models.Timer
        fields = ('name', 'start', 'end', 'duration', 'active', 'user')


class TummyTimeSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = models.TummyTime
        fields = ('child', 'start', 'end', 'duration', 'milestone')


class WeightSerializer(serializers.HyperlinkedModelSerializer):
    child = ChildSerializer()

    class Meta:
        model = models.Weight
        fields = ('child', 'weight', 'date')
