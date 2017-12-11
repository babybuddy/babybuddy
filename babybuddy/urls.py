# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views

from . import views

app_patterns = [
    url(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
    url('^password_reset/$', auth_views.PasswordResetView.as_view(),
        name='password_reset',),

    url(r'^$', views.RootRouter.as_view(), name='root-router'),
    url(r'^welcome/$', views.Welcome.as_view(), name='welcome'),

    url(r'^user/list/$', views.UserList.as_view(), name='user-list'),
    url(r'^user/add/$', views.UserAdd.as_view(), name='user-add'),
    url(r'^user/(?P<pk>[0-9]+)/$', views.UserUpdate.as_view(),
        name='user-update'),
    url(r'^user/(?P<pk>[0-9]+)/delete/$', views.UserDelete.as_view(),
        name='user-delete'),

    url(r'^user/password/$', views.UserPassword.as_view(),
        name='user-password'),
    url(r'^user/reset-api-key/$', views.UserResetAPIKey.as_view(),
        name='user-reset-api-key'),
    url(r'^user/settings/$', views.UserSettings.as_view(),
        name='user-settings'),
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include('api.urls', namespace='api')),
    url(r'', include((app_patterns, 'babybuddy'), namespace='babybuddy')),
    url(r'', include('core.urls', namespace='core')),
    url(r'', include('dashboard.urls', namespace='dashboard')),
    url(r'', include('reports.urls', namespace='reports')),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
