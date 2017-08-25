# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^reports/changes/(?P<slug>[^/.]+)/$',
        views.DiaperChangesChildReport.as_view(),
        name='report-diaperchange-child'),
    url(r'^reports/sleep/(?P<slug>[^/.]+)$',
        views.SleepChildReport.as_view(), name='report-sleep-child'),
]
