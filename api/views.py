# -*- coding: utf-8 -*-
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core import models

from . import serializers, filters
from .mixins import TimerFieldSupportMixin


class ChildViewSet(viewsets.ModelViewSet):
    queryset = models.Child.objects.all()
    serializer_class = serializers.ChildSerializer
    lookup_field = 'slug'
    filterset_fields = ('first_name', 'last_name', 'slug', 'birth_date')


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

    def __timer_operation(self, pk, func):
        try:
            timer = models.Timer.objects.get(pk=pk)
            return func(timer)
        except models.Timer.DoesNotExist:
            return Response(
                {"detail": "timer does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['patch'])
    def stop(self, request, pk=None):
        def do_stop(timer):
            if not timer.active:
                return Response(
                    {"detail": "timer already stopped"},
                    status=status.HTTP_412_PRECONDITION_FAILED
                )
            timer.stop()
            return Response({"detail": "timer stopped"})
        return self.__timer_operation(pk, do_stop)

    @action(detail=True, methods=['patch'])
    def restart(self, request, pk=None):
        def do_restart(timer):
            if timer.active:
                return Response(
                    {"detail": "timer already active"},
                    status=status.HTTP_412_PRECONDITION_FAILED
                )
            timer.restart()
            return Response({"detail": "timer restarted"})
        return self.__timer_operation(pk, do_restart)


class TummyTimeViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.TummyTime.objects.all()
    serializer_class = serializers.TummyTimeSerializer
    filterset_class = filters.TummyTimeFilter


class WeightViewSet(viewsets.ModelViewSet):
    queryset = models.Weight.objects.all()
    serializer_class = serializers.WeightSerializer
    filterset_fields = ('child', 'date')


class HeightViewSet(viewsets.ModelViewSet):
    queryset = models.Height.objects.all()
    serializer_class = serializers.HeightSerializer
    filterset_fields = ('child', 'date')


class HeadCircumferenceViewSet(viewsets.ModelViewSet):
    queryset = models.HeadCircumference.objects.all()
    serializer_class = serializers.HeadCircumferenceSerializer
    filterset_fields = ('child', 'date')


class BMIViewSet(viewsets.ModelViewSet):
    queryset = models.BMI.objects.all()
    serializer_class = serializers.BMISerializer
    filterset_fields = ('child', 'date')
