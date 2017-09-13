# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^reports/changes/types/(?P<slug>[^/.]+)/$',
        views.DiaperChangeTypesChildReport.as_view(),
        name='report-diaperchange-types-child'),

    url(r'^reports/sleep/pattern/(?P<slug>[^/.]+)$',
        views.SleepPatternChildReport.as_view(),
        name='report-sleep-pattern-child'),
    url(r'^reports/sleep/totals/(?P<slug>[^/.]+)$',
        views.SleepTotalsChildReport.as_view(),
        name='report-sleep-totals-child'),
]
