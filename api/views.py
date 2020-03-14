# -*- coding: utf-8 -*-
from rest_framework import viewsets

from core import models

from . import serializers
from .mixins import TimerFieldSupportMixin


class ChildViewSet(viewsets.ModelViewSet):
    queryset = models.Child.objects.all()
    serializer_class = serializers.ChildSerializer
    lookup_field = 'slug'
    filterset_fields = ('first_name', 'last_name', 'slug')


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = models.DiaperChange.objects.all()
    serializer_class = serializers.DiaperChangeSerializer
    filterset_fields = ('child', 'wet', 'solid', 'color', 'amount')


class FeedingViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.Feeding.objects.all()
    serializer_class = serializers.FeedingSerializer
    filterset_fields = ('child', 'type', 'method')


class NoteViewSet(viewsets.ModelViewSet):
    queryset = models.Note.objects.all()
    serializer_class = serializers.NoteSerializer
    filterset_fields = ('child',)


class SleepViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.Sleep.objects.all()
    serializer_class = serializers.SleepSerializer
    filterset_fields = ('child',)


class TemperatureViewSet(viewsets.ModelViewSet):
    queryset = models.Temperature.objects.all()
    serializer_class = serializers.TemperatureSerializer
    filterset_fields = ('child',)


class TimerViewSet(viewsets.ModelViewSet):
    queryset = models.Timer.objects.all()
    serializer_class = serializers.TimerSerializer
    filterset_fields = ('child', 'active', 'user')


class TummyTimeViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.TummyTime.objects.all()
    serializer_class = serializers.TummyTimeSerializer
    filterset_fields = ('child',)


class WeightViewSet(viewsets.ModelViewSet):
    queryset = models.Weight.objects.all()
    serializer_class = serializers.WeightSerializer
    filterset_fields = ('child',)
