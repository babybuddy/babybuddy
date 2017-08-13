# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from .views import (BabyViewSet, DiaperChangeViewSet, FeedingViewSet,
                    NoteViewSet, SleepViewSet, TummyTimeViewSet)

router = routers.DefaultRouter()
router.register(r'babies', BabyViewSet)
router.register(r'diaper-changes', DiaperChangeViewSet)
router.register(r'feedings', FeedingViewSet)
router.register(r'notes', NoteViewSet)
router.register(r'sleep', SleepViewSet)
router.register(r'tummy-times', TummyTimeViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework'))
]
