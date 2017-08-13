# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework import viewsets

from core.models import Baby, Sleep
from .serializers import (UserSerializer, BabySerializer, SleepSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class BabyViewSet(viewsets.ModelViewSet):
    queryset = Baby.objects.all()
    serializer_class = BabySerializer


class SleepViewSet(viewsets.ModelViewSet):
    queryset = Sleep.objects.all()
    serializer_class = SleepSerializer
