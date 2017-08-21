# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url('^password_reset/$', views.PasswordResetView.as_view(),
        name='password_reset',),

    url(r'', include('api.urls', namespace='api')),
    url(r'', include('core.urls')),
    url(r'', include('dashboard.urls')),
    url(r'', include('reports.urls')),
]
