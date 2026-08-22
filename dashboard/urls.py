# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", views.Dashboard.as_view(), name="dashboard"),
    path(
        "children/<str:slug>/dashboard/",
        views.ChildDashboard.as_view(),
        name="dashboard-child",
    ),
    path("dashboard/cards/", views.CustomizeCards.as_view(), name="dashboard-cards"),
    path("dashboard/reorder/", views.ReorderCards.as_view(), name="dashboard-reorder"),
]
