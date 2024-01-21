# -*- coding: utf-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path(
        "children/<str:slug>/dashboard/",
        views.MobileChildDashboard.as_view(),
        name="mobile-dashboard-child",
    ),
    path(
        "children/<str:slug>/changes/add",
        views.DiaperChangeAdd.as_view(),
    ),
]
