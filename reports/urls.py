# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^children/(?P<slug>[^/.]+)/reports/changes/lifetimes/$',
        views.DiaperChangeLifetimesChildReport.as_view(),
        name='report-diaperchange-lifetimes-child'),
    url(r'^children/(?P<slug>[^/.]+)/reports/changes/types/$',
        views.DiaperChangeTypesChildReport.as_view(),
        name='report-diaperchange-types-child'),

    url(r'^children/(?P<slug>[^/.]+)/reports/sleep/pattern/$',
        views.SleepPatternChildReport.as_view(),
        name='report-sleep-pattern-child'),
    url(r'^children/(?P<slug>[^/.]+)/reports/sleep/totals/$',
        views.SleepTotalsChildReport.as_view(),
        name='report-sleep-totals-child'),

    url(r'^children/(?P<slug>[^/.]+)/reports/weight/weight/$',
        views.WeightWeightChildReoport.as_view(),
        name='report-weight-weight-child'),
]
