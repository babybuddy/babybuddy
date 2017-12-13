# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),
    path(
        'children/<slug:slug>/dashboard/',
        views.ChildDashboard.as_view(),
        name='dashboard-child'
    ),
]
