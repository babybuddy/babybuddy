# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.Dashboard.as_view(), name='index'),

    url(r'children/$', views.ChildList.as_view(), name='child-list'),
    url(r'children/add/$', views.ChildAdd.as_view(), name='child-add'),
    url(r'children/(?P<pk>[0-9]+)/$', views.ChildUpdate.as_view(),
        name='child-update'),
    url(r'children/(?P<pk>[0-9]+)/delete/$', views.ChildDelete.as_view(),
        name='child-delete'),

    url(r'changes/$', views.DiaperChangeList.as_view(),
        name='diaperchange-list'),
    url(r'changes/add/$', views.DiaperChangeAdd.as_view(),
        name='diaperchange-add'),
    url(r'changes/(?P<pk>[0-9]+)/$', views.DiaperChangeUpdate.as_view(),
        name='diaperchange-update'),
    url(r'changes/(?P<pk>[0-9]+)/delete/$', views.DiaperChangeDelete.as_view(),
        name='diaperchange-delete'),

    url(r'feedings/$', views.FeedingList.as_view(), name='feeding-list'),
    url(r'feedings/add/$', views.FeedingAdd.as_view(), name='feeding-add'),
    url(r'feedings/(?P<pk>[0-9]+)/$', views.FeedingUpdate.as_view(),
        name='feeding-update'),
    url(r'feedings/(?P<pk>[0-9]+)/delete/$', views.FeedingDelete.as_view(),
        name='feeding-delete'),

    url(r'notes/$', views.NoteList.as_view(), name='note-list'),
    url(r'notes/add/$', views.NoteAdd.as_view(), name='note-add'),
    url(r'notes/(?P<pk>[0-9]+)/$', views.NoteUpdate.as_view(),
        name='note-update'),
    url(r'notes/(?P<pk>[0-9]+)/delete/$', views.NoteDelete.as_view(),
        name='note-delete'),

    url(r'sleep/$', views.SleepList.as_view(), name='sleep-list'),
    url(r'sleep/add/$', views.SleepAdd.as_view(), name='sleep-add'),
    url(r'sleep/(?P<pk>[0-9]+)/$', views.SleepUpdate.as_view(),
        name='sleep-update'),
    url(r'sleep/(?P<pk>[0-9]+)/delete/$', views.SleepDelete.as_view(),
        name='sleep-delete'),

    url(r'timer/add/$', views.TimerAdd.as_view(), name='timer-add'),

    url(r'tummy-time/$', views.TummyTimeList.as_view(), name='tummytime-list'),
    url(r'tummy-time/add/$', views.TummyTimeAdd.as_view(),
        name='tummytime-add'),
    url(r'tummy-time/(?P<pk>[0-9]+)/$', views.TummyTimeUpdate.as_view(),
        name='tummytime-update'),
    url(r'tummy-time/(?P<pk>[0-9]+)/delete/$', views.TummyTimeDelete.as_view(),
        name='tummytime-delete'),
]
