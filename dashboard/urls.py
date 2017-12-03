# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views

app_name = 'dashboard'

urlpatterns = [
    url(r'^dashboard/$', views.Dashboard.as_view(), name='dashboard'),
    url(r'^children/(?P<slug>[^/.]+)/dashboard/$',
        views.ChildDashboard.as_view(), name='dashboard-child'),
]
