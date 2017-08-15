# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'baby/add/$', views.BabyAdd.as_view(), name='baby-add'),
    url(r'baby/(?P<pk>[0-9]+)/$', views.BabyUpdate.as_view(),
        name='baby-update'),
    url(r'baby/(?P<pk>[0-9]+)/delete/$', views.BabyDelete.as_view(),
        name='baby-delete'),
]
