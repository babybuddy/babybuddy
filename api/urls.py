# -*- coding: utf-8 -*-
from typing import NamedTuple, Optional, Any

from django.urls import include, path
from rest_framework import routers
from rest_framework.schemas import get_schema_view

from . import views

router = routers.DefaultRouter()
router.register(r"bmi", views.BMIViewSet)
router.register(r"changes", views.DiaperChangeViewSet)
router.register(r"children", views.ChildViewSet)
router.register(r"feedings", views.FeedingViewSet)
router.register(r"head-circumference", views.HeadCircumferenceViewSet)
router.register(r"height", views.HeightViewSet)
router.register(r"notes", views.NoteViewSet)
router.register(r"pumping", views.PumpingViewSet)
router.register(r"sleep", views.SleepViewSet)
router.register(r"tags", views.TagViewSet)
router.register(r"temperature", views.TemperatureViewSet)
router.register(r"timers", views.TimerViewSet)
router.register(r"tummy-times", views.TummyTimeViewSet)
router.register(r"weight", views.WeightViewSet)

class ExtraUrl(NamedTuple):
    view: Any
    name: Optional[str] = None

extra_api_urls = [
    path("api/profile", views.ProfileView.as_view()),
    path(
        "api/schema", 
        get_schema_view(
            title="Baby Buddy API",
            version=1,
            description="API documentation for the Baby Buddy application",
        ),
        name="openapi-schema",
    ),
]

app_name = "api"


urlpatterns = [
    path("api/", include(router.urls + list(extra_api_urls))),
    path("api/auth/", include("rest_framework.urls", namespace="rest_framework")),
] + extra_api_urls
