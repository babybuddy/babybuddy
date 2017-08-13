# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets

from core.models import Baby, DiaperChange, Feeding, Sleep, TummyTime
from core.utils import filter_by_params
from .serializers import (BabySerializer, DiaperChangeSerializer,
                          FeedingSerializer, SleepSerializer,
                          TummyTimeSerializer,)


class BabyViewSet(viewsets.ModelViewSet):
    queryset = Baby.objects.all()
    serializer_class = BabySerializer

    def get_queryset(self):
        params = ['first_name', 'last_name']
        return filter_by_params(self.request, Baby, params)


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = DiaperChange.objects.all()
    serializer_class = DiaperChangeSerializer

    def get_queryset(self):
        params = ['baby__last_name', 'wet', 'solid', 'color']
        return filter_by_params(self.request, DiaperChange, params)


class FeedingViewSet(viewsets.ModelViewSet):
    queryset = Feeding.objects.all()
    serializer_class = FeedingSerializer

    def get_queryset(self):
        params = ['baby__last_name', 'type', 'method']
        return filter_by_params(self.request, Feeding, params)


class SleepViewSet(viewsets.ModelViewSet):
    queryset = Sleep.objects.all()
    serializer_class = SleepSerializer

    def get_queryset(self):
        params = ['baby__last_name']
        return filter_by_params(self.request, Sleep, params)


class TummyTimeViewSet(viewsets.ModelViewSet):
    queryset = TummyTime.objects.all()
    serializer_class = TummyTimeSerializer

    def get_queryset(self):
        params = ['baby__last_name']
        return filter_by_params(self.request, TummyTime, params)
