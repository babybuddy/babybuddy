# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('children/', views.ChildList.as_view(), name='child-list'),
    path('children/add/', views.ChildAdd.as_view(), name='child-add'),
    path('children/<slug:slug>/', views.ChildDetail.as_view(), name='child'),
    path(
        'children/<slug:slug>/edit/',
        views.ChildUpdate.as_view(),
        name='child-update'
    ),
    path(
        'children/<slug:slug>/delete/',
        views.ChildDelete.as_view(),
        name='child-delete'
    ),

    path(
        'changes/',
        views.DiaperChangeList.as_view(),
        name='diaperchange-list'
    ),
    path(
        'changes/add/',
        views.DiaperChangeAdd.as_view(),
        name='diaperchange-add'
    ),
    path(
        'changes/<int:pk>/',
        views.DiaperChangeUpdate.as_view(),
        name='diaperchange-update'
    ),
    path(
        'changes/<int:pk>/delete/',
        views.DiaperChangeDelete.as_view(),
        name='diaperchange-delete'
    ),

    path('feedings/', views.FeedingList.as_view(), name='feeding-list'),
    path('feedings/add/', views.FeedingAdd.as_view(), name='feeding-add'),
    path(
        'feedings/<int:pk>/',
        views.FeedingUpdate.as_view(),
        name='feeding-update'
    ),
    path(
        'feedings/<int:pk>/delete/',
        views.FeedingDelete.as_view(),
        name='feeding-delete'
    ),

    path('notes/', views.NoteList.as_view(), name='note-list'),
    path('notes/add/', views.NoteAdd.as_view(), name='note-add'),
    path('notes/<int:pk>/', views.NoteUpdate.as_view(), name='note-update'),
    path(
        'notes/<int:pk>/delete/',
        views.NoteDelete.as_view(),
        name='note-delete'
    ),

    path('sleep/', views.SleepList.as_view(), name='sleep-list'),
    path('sleep/add/', views.SleepAdd.as_view(), name='sleep-add'),
    path('sleep/<int:pk>/', views.SleepUpdate.as_view(), name='sleep-update'),
    path(
        'sleep/<int:pk>/delete/',
        views.SleepDelete.as_view(),
        name='sleep-delete'
    ),

    path('timers/', views.TimerList.as_view(), name='timer-list'),
    path('timer/add/', views.TimerAdd.as_view(), name='timer-add'),
    path(
        'timer/add/quick/',
        views.TimerAddQuick.as_view(),
        name='timer-add-quick'
    ),
    path('timer/<int:pk>/', views.TimerDetail.as_view(), name='timer-detail'),
    path(
        'timer/<int:pk>/edit/',
        views.TimerUpdate.as_view(),
        name='timer-update'
    ),
    path(
        'timer/<int:pk>/delete/',
        views.TimerDelete.as_view(),
        name='timer-delete'
    ),
    path('timer/<int:pk>/stop/', views.TimerStop.as_view(), name='timer-stop'),
    path(
        'timer/<int:pk>/restart/',
        views.TimerRestart.as_view(),
        name='timer-restart'
    ),

    path('tummy-time/', views.TummyTimeList.as_view(), name='tummytime-list'),
    path(
        'tummy-time/add/',
        views.TummyTimeAdd.as_view(),
        name='tummytime-add'
    ),
    path(
        'tummy-time/<int:pk>/',
        views.TummyTimeUpdate.as_view(),
        name='tummytime-update'
    ),
    path(
        'tummy-time/<int:pk>/delete/',
        views.TummyTimeDelete.as_view(),
        name='tummytime-delete'
    ),

    path('weight/', views.WeightList.as_view(), name='weight-list'),
    path('weight/add/', views.WeightAdd.as_view(), name='weight-add'),
    path(
        'weight/<int:pk>/',
        views.WeightUpdate.as_view(),
        name='weight-update'
    ),
    path(
        'weight/<int:pk>/delete/',
        views.WeightDelete.as_view(),
        name='weight-delete'
    ),
]
