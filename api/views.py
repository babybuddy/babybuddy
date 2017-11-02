# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets

from core.models import (Child, DiaperChange, Feeding, Note, Sleep, Timer,
                         TummyTime)

from .serializers import (ChildSerializer, DiaperChangeSerializer,
                          FeedingSerializer, NoteSerializer, SleepSerializer,
                          TimerSerializer, TummyTimeSerializer,)


class ChildViewSet(viewsets.ModelViewSet):
    queryset = Child.objects.all()
    serializer_class = ChildSerializer
    lookup_field = 'slug'
    filter_fields = ('first_name', 'last_name', 'slug')


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = DiaperChange.objects.all()
    serializer_class = DiaperChangeSerializer
    filter_fields = ('child', 'wet', 'solid', 'color')


class FeedingViewSet(viewsets.ModelViewSet):
    queryset = Feeding.objects.all()
    serializer_class = FeedingSerializer
    filter_fields = ('child', 'type', 'method')


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filter_fields = ('child',)


class SleepViewSet(viewsets.ModelViewSet):
    queryset = Sleep.objects.all()
    serializer_class = SleepSerializer
    filter_fields = ('child',)


class TimerViewSet(viewsets.ModelViewSet):
    queryset = Timer.objects.all()
    serializer_class = TimerSerializer
    filter_fields = ('active', 'user')


class TummyTimeViewSet(viewsets.ModelViewSet):
    queryset = TummyTime.objects.all()
    serializer_class = TummyTimeSerializer
    filter_fields = ('child',)
