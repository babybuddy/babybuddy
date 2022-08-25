# -*- coding: utf-8 -*-
from collections import OrderedDict

from typing import NamedTuple, List, Any

from django.urls import include, path
from rest_framework import routers
from rest_framework.schemas import get_schema_view

from . import views


class ExtraPath(NamedTuple):
    path: str
    reverese_name: str
    route: Any


class CustomRouterWithExtraPaths(routers.DefaultRouter):
    extra_api_urls: List[ExtraPath]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_api_urls = []

    def add_detail_path(self, url_path, reverese_name, *args, **kwargs):
        self.extra_api_urls = self.extra_api_urls or []
        kwargs["name"] = reverese_name
        self.extra_api_urls.append(
            ExtraPath(url_path, reverese_name, path(url_path, *args, **kwargs))
        )

    def get_api_root_view(self, api_urls=None):
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)
        for extra_path in self.extra_api_urls:
            api_root_dict[extra_path.path] = extra_path.reverese_name

        return self.APIRootView.as_view(api_root_dict=api_root_dict)

    @property
    def urls(self):
        return super().urls + [e.route for e in self.extra_api_urls]


router = CustomRouterWithExtraPaths()
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

router.add_detail_path("profile", "profile", views.ProfileView.as_view())
router.add_detail_path(
    "schema",
    "openapi-schema",
    get_schema_view(
        title="Baby Buddy API",
        version=1,
        description="API documentation for the Baby Buddy application",
    ),
)


app_name = "api"

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/auth/", include("rest_framework.urls", namespace="rest_framework")),
]
