# -*- coding: utf-8 -*-
from rest_framework import serializers

from django.contrib.auth.models import User

from core import models


class CoreModelSerializer(serializers.HyperlinkedModelSerializer):
    """
    Provide the child link (used by most core models) and run model clean()
    methods during POST operations.
    """
    child = serializers.PrimaryKeyRelatedField(
        queryset=models.Child.objects.all())

    def validate(self, attrs):
        instance = self.Meta.model(**attrs)
        instance.clean()
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class ChildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Child
        fields = ('id', 'first_name', 'last_name', 'birth_date', 'slug',
                  'picture')
        lookup_field = 'slug'


class DiaperChangeSerializer(CoreModelSerializer):
    class Meta:
        model = models.DiaperChange
        fields = ('id', 'child', 'time', 'wet', 'solid', 'color', 'amount')


class FeedingSerializer(CoreModelSerializer):
    class Meta:
        model = models.Feeding
        fields = ('id', 'child', 'start', 'end', 'duration', 'type', 'method',
                  'amount')


class NoteSerializer(CoreModelSerializer):
    class Meta:
        model = models.Note
        fields = ('id', 'child', 'note', 'time')


class SleepSerializer(CoreModelSerializer):
    class Meta:
        model = models.Sleep
        fields = ('id', 'child', 'start', 'end', 'duration', 'nap')


class TemperatureSerializer(CoreModelSerializer):
    class Meta:
        model = models.Temperature
        fields = ('id', 'child', 'temperature', 'time')


class TimerSerializer(CoreModelSerializer):
    child = serializers.PrimaryKeyRelatedField(
        allow_null=True, allow_empty=True, queryset=models.Child.objects.all(),
        required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = models.Timer
        fields = ('id', 'child', 'name', 'start', 'end', 'duration', 'active',
                  'user')


class TummyTimeSerializer(CoreModelSerializer):
    class Meta:
        model = models.TummyTime
        fields = ('id', 'child', 'start', 'end', 'duration', 'milestone')


class WeightSerializer(CoreModelSerializer):
    class Meta:
        model = models.Weight
        fields = ('id', 'child', 'weight', 'date')
