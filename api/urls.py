# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from . import views


router = routers.DefaultRouter()
router.register(r'children', views.ChildViewSet)
router.register(r'changes', views.DiaperChangeViewSet)
router.register(r'feedings', views.FeedingViewSet)
router.register(r'notes', views.NoteViewSet)
router.register(r'sleep', views.SleepViewSet)
router.register(r'timers', views.TimerViewSet)
router.register(r'tummy-times', views.TummyTimeViewSet)
router.register(r'weight', views.WeightViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api/auth/', include('rest_framework.urls',
                               namespace='rest_framework'))
]
