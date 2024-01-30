# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = "mobile"


urlpatterns = [
    path(
        "children/<str:slug>/dashboard/",
        views.MobileChildDashboard.as_view(),
        name="mobile-dashboard-child",
    ),
    path(
        "children/<str:slug>/changes/add",
        views.MobileDiaperChangeAdd.as_view(),
        name="changes-add",
    ),
    path(
        "children/<str:slug>/feeding/bottle/add",
        views.MobileBottleFeedingAdd.as_view(),
        name="bottle-feeding-add",
    ),
]
