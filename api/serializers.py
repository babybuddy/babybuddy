# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework import serializers

from core.models import Baby, Sleep


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')


class BabySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Baby
        fields = ('first_name', 'last_name', 'birth_date')


class SleepSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sleep
        fields = ('baby', 'start', 'end')
