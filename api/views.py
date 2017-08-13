# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework import viewsets

from core.models import Baby, DiaperChange, Feeding, Sleep, TummyTime
from .serializers import (BabySerializer, DiaperChangeSerializer,
                          FeedingSerializer, SleepSerializer,
                          TummyTimeSerializer, UserSerializer,)


class BabyViewSet(viewsets.ModelViewSet):
    queryset = Baby.objects.all()
    serializer_class = BabySerializer

    def get_queryset(self):
        queryset = Baby.objects.all()

        for param in ['first_name', 'last_name']:
            value = self.request.query_params.get(param, None)
            if value is not None:
                queryset = queryset.filter(**{param: value})

        return queryset


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = DiaperChange.objects.all()
    serializer_class = DiaperChangeSerializer

    def get_queryset(self):
        queryset = DiaperChange.objects.all()

        for param in ['baby__last_name', 'wet', 'solid', 'color']:
            value = self.request.query_params.get(param, None)
            if value is not None:
                queryset = queryset.filter(**{param: value})

        return queryset


class FeedingViewSet(viewsets.ModelViewSet):
    queryset = Feeding.objects.all()
    serializer_class = FeedingSerializer

    def get_queryset(self):
        queryset = Feeding.objects.all()

        for param in ['baby__last_name', 'type', 'method']:
            value = self.request.query_params.get(param, None)
            if value is not None:
                queryset = queryset.filter(**{param: value})

        return queryset


class SleepViewSet(viewsets.ModelViewSet):
    queryset = Sleep.objects.all()
    serializer_class = SleepSerializer

    def get_queryset(self):
        queryset = Sleep.objects.all()

        for param in ['baby__last_name']:
            value = self.request.query_params.get(param, None)
            if value is not None:
                queryset = queryset.filter(**{param: value})

        return queryset


class TummyTimeViewSet(viewsets.ModelViewSet):
    queryset = TummyTime.objects.all()
    serializer_class = TummyTimeSerializer

    def get_queryset(self):
        queryset = TummyTime.objects.all()

        for param in ['baby__last_name']:
            value = self.request.query_params.get(param, None)
            if value is not None:
                queryset = queryset.filter(**{param: value})

        return queryset


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
