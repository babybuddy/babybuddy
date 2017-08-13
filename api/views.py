# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework import viewsets

from core.models import Baby, Feeding, Sleep, TummyTime
from .serializers import (BabySerializer, FeedingSerializer, SleepSerializer,
                          TummyTimeSerializer, UserSerializer,)


class BabyViewSet(viewsets.ModelViewSet):
    queryset = Baby.objects.all()
    serializer_class = BabySerializer


class FeedingViewSet(viewsets.ModelViewSet):
    queryset = Feeding.objects.all()
    serializer_class = FeedingSerializer


class SleepViewSet(viewsets.ModelViewSet):
    queryset = Sleep.objects.all()
    serializer_class = SleepSerializer


class TummyTimeViewSet(viewsets.ModelViewSet):
    queryset = TummyTime.objects.all()
    serializer_class = TummyTimeSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
