# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin

from core import views

urlpatterns = [
    url(r'^baby/new/$', views.BabyFormView.as_view(), name='baby_new'),

    url(r'^admin/', admin.site.urls),
    url(r'', include('api.urls')),
]
