# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core import models

from . import serializers, filters
from .mixins import TimerFieldSupportMixin


class ChildViewSet(viewsets.ModelViewSet):
    queryset = models.Child.objects.all()
    serializer_class = serializers.ChildSerializer
    lookup_field = "slug"
    filterset_fields = ("first_name", "last_name", "slug", "birth_date")


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = models.DiaperChange.objects.all()
    serializer_class = serializers.DiaperChangeSerializer
    filterset_class = filters.DiaperChangeFilter


class FeedingViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.Feeding.objects.all()
    serializer_class = serializers.FeedingSerializer
    filterset_class = filters.FeedingFilter


class NoteViewSet(viewsets.ModelViewSet):
    queryset = models.Note.objects.all()
    serializer_class = serializers.NoteSerializer
    filterset_class = filters.NoteFilter


class SleepViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.Sleep.objects.all()
    serializer_class = serializers.SleepSerializer
    filterset_class = filters.SleepFilter


class TemperatureViewSet(viewsets.ModelViewSet):
    queryset = models.Temperature.objects.all()
    serializer_class = serializers.TemperatureSerializer
    filterset_class = filters.TemperatureFilter


class TimerViewSet(viewsets.ModelViewSet):
    queryset = models.Timer.objects.all()
    serializer_class = serializers.TimerSerializer
    filterset_class = filters.TimerFilter

    @action(detail=True, methods=["patch"])
    def stop(self, request, pk=None):
        timer = self.get_object()
        timer.stop()
        return Response(self.serializer_class(timer).data)

    @action(detail=True, methods=["patch"])
    def restart(self, request, pk=None):
        timer = self.get_object()
        timer.restart()
        return Response(self.serializer_class(timer).data)


class TummyTimeViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.TummyTime.objects.all()
    serializer_class = serializers.TummyTimeSerializer
    filterset_class = filters.TummyTimeFilter


class WeightViewSet(viewsets.ModelViewSet):
    queryset = models.Weight.objects.all()
    serializer_class = serializers.WeightSerializer
    filterset_fields = ("child", "date")


class HeightViewSet(viewsets.ModelViewSet):
    queryset = models.Height.objects.all()
    serializer_class = serializers.HeightSerializer
    filterset_fields = ("child", "date")


class HeadCircumferenceViewSet(viewsets.ModelViewSet):
    queryset = models.HeadCircumference.objects.all()
    serializer_class = serializers.HeadCircumferenceSerializer
    filterset_fields = ("child", "date")


class BMIViewSet(viewsets.ModelViewSet):
    queryset = models.BMI.objects.all()
    serializer_class = serializers.BMISerializer
    filterset_fields = ("child", "date")
