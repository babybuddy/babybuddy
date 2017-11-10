# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets

from core import models

from . import serializers


class ChildViewSet(viewsets.ModelViewSet):
    queryset = models.Child.objects.all()
    serializer_class = serializers.ChildSerializer
    lookup_field = 'slug'
    filter_fields = ('first_name', 'last_name', 'slug')


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = models.DiaperChange.objects.all()
    serializer_class = serializers.DiaperChangeSerializer
    filter_fields = ('child', 'wet', 'solid', 'color')


class FeedingViewSet(viewsets.ModelViewSet):
    queryset = models.Feeding.objects.all()
    serializer_class = serializers.FeedingSerializer
    filter_fields = ('child', 'type', 'method')


class NoteViewSet(viewsets.ModelViewSet):
    queryset = models.Note.objects.all()
    serializer_class = serializers.NoteSerializer
    filter_fields = ('child',)


class SleepViewSet(viewsets.ModelViewSet):
    queryset = models.Sleep.objects.all()
    serializer_class = serializers.SleepSerializer
    filter_fields = ('child',)


class TimerViewSet(viewsets.ModelViewSet):
    queryset = models.Timer.objects.all()
    serializer_class = serializers.TimerSerializer
    filter_fields = ('active', 'user')


class TummyTimeViewSet(viewsets.ModelViewSet):
    queryset = models.TummyTime.objects.all()
    serializer_class = serializers.TummyTimeSerializer
    filter_fields = ('child',)


class WeightViewSet(viewsets.ModelViewSet):
    queryset = models.Weight.objects.all()
    serializer_class = serializers.WeightSerializer
    filter_fields = ('child',)
