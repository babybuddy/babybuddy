# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^reports/(?P<slug>[^/.]+)/sleep/$',
        views.SleepReport.as_view(), name='report-sleep'),
]
