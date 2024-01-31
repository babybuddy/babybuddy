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
        "changes/add",
        views.MobileDiaperChangeAdd.as_view(),
        name="changes-add",
    ),
    path(
        "feeding/bottle/add",
        views.MobileBottleFeedingAdd.as_view(),
        name="bottle-feeding-add",
    ),
    path(
        "pumping/add",
        views.MobilePumpingAdd.as_view(),
        name="pumping-add",
    ),
]
