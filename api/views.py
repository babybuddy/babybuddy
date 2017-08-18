# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets

from core.models import (Child, DiaperChange, Feeding, Note, Sleep, Timer,
                         TummyTime)
from core.utils import filter_by_params

from .serializers import (ChildSerializer, DiaperChangeSerializer,
                          FeedingSerializer, NoteSerializer, SleepSerializer,
                          TimerSerializer, TummyTimeSerializer,)


class ChildViewSet(viewsets.ModelViewSet):
    queryset = Child.objects.all()
    serializer_class = ChildSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        params = ['first_name', 'last_name', 'slug']
        return filter_by_params(self.request, Child, params)


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = DiaperChange.objects.all()
    serializer_class = DiaperChangeSerializer

    def get_queryset(self):
        params = ['child__last_name', 'wet', 'solid', 'color']
        return filter_by_params(self.request, DiaperChange, params)


class FeedingViewSet(viewsets.ModelViewSet):
    queryset = Feeding.objects.all()
    serializer_class = FeedingSerializer

    def get_queryset(self):
        params = ['child__last_name', 'type', 'method', 'amount']
        return filter_by_params(self.request, Feeding, params)


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    def get_queryset(self):
        params = ['child__last_name']
        return filter_by_params(self.request, Note, params)


class SleepViewSet(viewsets.ModelViewSet):
    queryset = Sleep.objects.all()
    serializer_class = SleepSerializer

    def get_queryset(self):
        params = ['child__last_name']
        return filter_by_params(self.request, Sleep, params)


class TimerViewSet(viewsets.ModelViewSet):
    queryset = Timer.objects.all()
    serializer_class = TimerSerializer

    def get_queryset(self):
        params = ['name', 'active', 'user']
        return filter_by_params(self.request, Timer, params)


class TummyTimeViewSet(viewsets.ModelViewSet):
    queryset = TummyTime.objects.all()
    serializer_class = TummyTimeSerializer

    def get_queryset(self):
        params = ['child__last_name']
        return filter_by_params(self.request, TummyTime, params)
