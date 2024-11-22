# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # BMI
    path("bmi/", views.BMIList.as_view(), name="bmi-list"),
    path("bmi/add/", views.BMIAdd.as_view(), name="bmi-add"),
    path("bmi/<int:pk>/", views.BMIUpdate.as_view(), name="bmi-update"),
    path("bmi/<int:pk>/delete/", views.BMIDelete.as_view(), name="bmi-delete"),
    path("bmi/<int:pk>/history/", views.BMIHistory.as_view(), name="bmi-history"),
    # Child
    path("children/", views.ChildList.as_view(), name="child-list"),
    path("children/add/", views.ChildAdd.as_view(), name="child-add"),
    path("children/<str:slug>/", views.ChildDetail.as_view(), name="child"),
    path("children/<str:slug>/edit/", views.ChildUpdate.as_view(), name="child-update"),
    path(
        "children/<str:slug>/delete/", views.ChildDelete.as_view(), name="child-delete"
    ),
    path(
        "children/<str:slug>/history/",
        views.ChildHistory.as_view(),
        name="child-history",
    ),
    path("timeline/", views.Timeline.as_view(), name="timeline"),
    # Diaper Changes
    path("changes/", views.DiaperChangeList.as_view(), name="diaperchange-list"),
    path("changes/add/", views.DiaperChangeAdd.as_view(), name="diaperchange-add"),
    path(
        "changes/<int:pk>/",
        views.DiaperChangeUpdate.as_view(),
        name="diaperchange-update",
    ),
    path(
        "changes/<int:pk>/delete/",
        views.DiaperChangeDelete.as_view(),
        name="diaperchange-delete",
    ),
    path(
        "changes/<int:pk>/history",
        views.DiaperChangeHistory.as_view(),
        name="diaperchange-history",
    ),
    # Feedings
    path(
        "feedings/bottle/add/",
        views.BottleFeedingAdd.as_view(),
        name="bottle-feeding-add",
    ),
    path("feedings/", views.FeedingList.as_view(), name="feeding-list"),
    path("feedings/add/", views.FeedingAdd.as_view(), name="feeding-add"),
    path("feedings/<int:pk>/", views.FeedingUpdate.as_view(), name="feeding-update"),
    path(
        "feedings/<int:pk>/delete/",
        views.FeedingDelete.as_view(),
        name="feeding-delete",
    ),
    path(
        "feedings/<int:pk>/history/",
        views.FeedingHistory.as_view(),
        name="feeding-history",
    ),
    # Head Circumference
    path(
        "head-circumference/",
        views.HeadCircumferenceList.as_view(),
        name="head-circumference-list",
    ),
    path(
        "head-circumference/add/",
        views.HeadCircumferenceAdd.as_view(),
        name="head-circumference-add",
    ),
    path(
        "head-circumference/<int:pk>/",
        views.HeadCircumferenceUpdate.as_view(),
        name="head-circumference-update",
    ),
    path(
        "head-circumference/<int:pk>/delete/",
        views.HeadCircumferenceDelete.as_view(),
        name="head-circumference-delete",
    ),
    path(
        "head-circumference/<int:pk>/history/",
        views.HeadCircumferenceHistory.as_view(),
        name="head-circumference-history",
    ),
    # Height
    path("height/", views.HeightList.as_view(), name="height-list"),
    path("height/add/", views.HeightAdd.as_view(), name="height-add"),
    path("height/<int:pk>/", views.HeightUpdate.as_view(), name="height-update"),
    path("height/<int:pk>/delete/", views.HeightDelete.as_view(), name="height-delete"),
    path(
        "height/<int:pk>/history/", views.HeightHistory.as_view(), name="height-history"
    ),
    # Notes
    path("notes/", views.NoteList.as_view(), name="note-list"),
    path("notes/add/", views.NoteAdd.as_view(), name="note-add"),
    path("notes/<int:pk>/", views.NoteUpdate.as_view(), name="note-update"),
    path("notes/<int:pk>/delete/", views.NoteDelete.as_view(), name="note-delete"),
    path("notes/<int:pk>/history/", views.NoteHistory.as_view(), name="note-history"),
    # Pumping
    path("pumping/", views.PumpingList.as_view(), name="pumping-list"),
    path("pumping/add/", views.PumpingAdd.as_view(), name="pumping-add"),
    path(
        "pumping/<int:pk>/",
        views.PumpingUpdate.as_view(),
        name="pumping-update",
    ),
    path(
        "pumping/<int:pk>/delete/",
        views.PumpingDelete.as_view(),
        name="pumping-delete",
    ),
    path(
        "pumping/<int:pk>/history/",
        views.PumpingHistory.as_view(),
        name="pumping-history",
    ),
    # Sleep
    path("sleep/", views.SleepList.as_view(), name="sleep-list"),
    path("sleep/add/", views.SleepAdd.as_view(), name="sleep-add"),
    path("sleep/<int:pk>/", views.SleepUpdate.as_view(), name="sleep-update"),
    path("sleep/<int:pk>/delete/", views.SleepDelete.as_view(), name="sleep-delete"),
    path("sleep/<int:pk>/history/", views.SleepHistory.as_view(), name="sleep-history"),
    # Tags
    path("tags/", views.TagAdminList.as_view(), name="tag-list"),
    path("tags/add/", views.TagAdminAdd.as_view(), name="tag-add"),
    path("tags/<str:slug>/", views.TagAdminDetail.as_view(), name="tag"),
    path("tags/<str:slug>/edit", views.TagAdminUpdate.as_view(), name="tag-update"),
    path("tags/<str:slug>/delete/", views.TagAdminDelete.as_view(), name="tag-delete"),
    path(
        "tags/<str:slug>/history/", views.TagAdminHistory.as_view(), name="tag-history"
    ),
    # Temperature
    path("temperature/", views.TemperatureList.as_view(), name="temperature-list"),
    path("temperature/add/", views.TemperatureAdd.as_view(), name="temperature-add"),
    path(
        "temperature/<int:pk>/",
        views.TemperatureUpdate.as_view(),
        name="temperature-update",
    ),
    path(
        "temperature/<int:pk>/delete/",
        views.TemperatureDelete.as_view(),
        name="temperature-delete",
    ),
    path(
        "temperature/<int:pk>/history/",
        views.TemperatureHistory.as_view(),
        name="temperature-history",
    ),
    # Timers
    path("timers/", views.TimerList.as_view(), name="timer-list"),
    path("timers/add/", views.TimerAdd.as_view(), name="timer-add"),
    path("timers/add/quick/", views.TimerAddQuick.as_view(), name="timer-add-quick"),
    path("timers/<int:pk>/", views.TimerDetail.as_view(), name="timer-detail"),
    path("timers/<int:pk>/edit/", views.TimerUpdate.as_view(), name="timer-update"),
    path("timers/<int:pk>/delete/", views.TimerDelete.as_view(), name="timer-delete"),
    path(
        "timers/<int:pk>/restart/", views.TimerRestart.as_view(), name="timer-restart"
    ),
    path(
        "timers/<int:pk>/history/", views.TimerHistory.as_view(), name="timer-history"
    ),
    # Tummy Time
    path("tummy-time/", views.TummyTimeList.as_view(), name="tummytime-list"),
    path("tummy-time/add/", views.TummyTimeAdd.as_view(), name="tummytime-add"),
    path(
        "tummy-time/<int:pk>/", views.TummyTimeUpdate.as_view(), name="tummytime-update"
    ),
    path(
        "tummy-time/<int:pk>/delete/",
        views.TummyTimeDelete.as_view(),
        name="tummytime-delete",
    ),
    path(
        "tummy-time/<int:pk>/history/",
        views.TummyTimeHistory.as_view(),
        name="tummytime-history",
    ),
    # Weight
    path("weight/", views.WeightList.as_view(), name="weight-list"),
    path("weight/add/", views.WeightAdd.as_view(), name="weight-add"),
    path("weight/<int:pk>/", views.WeightUpdate.as_view(), name="weight-update"),
    path("weight/<int:pk>/delete/", views.WeightDelete.as_view(), name="weight-delete"),
    path(
        "weight/<int:pk>/history/", views.WeightHistory.as_view(), name="weight-history"
    ),
]
