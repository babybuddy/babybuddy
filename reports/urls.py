# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path(
        'children/<str:slug>/reports/changes/amounts/',
        views.DiaperChangeAmounts.as_view(),
        name='report-diaperchange-amounts-child'
    ),
    path(
        'children/<str:slug>/reports/changes/lifetimes/',
        views.DiaperChangeLifetimesChildReport.as_view(),
        name='report-diaperchange-lifetimes-child'
    ),
    path(
        'children/<str:slug>/reports/changes/types/',
        views.DiaperChangeTypesChildReport.as_view(),
        name='report-diaperchange-types-child'
    ),
    path(
        'children/<str:slug>/reports/feeding/amounts/',
        views.FeedingAmountsChildReport.as_view(),
        name='report-feeding-amounts-child'
    ),
    path(
        'children/<str:slug>/reports/feeding/duration/',
        views.FeedingDurationChildReport.as_view(),
        name='report-feeding-duration-child'
    ),
    path(
        'children/<str:slug>/reports/sleep/pattern/',
        views.SleepPatternChildReport.as_view(),
        name='report-sleep-pattern-child'
    ),
    path(
        'children/<str:slug>/reports/sleep/totals/',
        views.SleepTotalsChildReport.as_view(),
        name='report-sleep-totals-child'
    ),
    path(
        'children/<str:slug>/reports/weight/weight/',
        views.WeightWeightChildReport.as_view(),
        name='report-weight-weight-child'
    ),
]
