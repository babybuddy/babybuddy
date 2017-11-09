# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
    url('^password_reset/$', auth_views.PasswordResetView.as_view(),
        name='password_reset',),

    url(r'^$', views.RootRouter.as_view(), name='root-router'),
    url(r'^welcome/$', views.Welcome.as_view(), name='welcome'),

    url(r'', include('api.urls', namespace='api')),
    url(r'', include('core.urls')),
    url(r'', include('dashboard.urls')),
    url(r'', include('reports.urls', namespace='reports')),
]
