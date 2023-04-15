# -*- coding: utf-8 -*-
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy

from . import views

app_patterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "reset/",
        auth_views.PasswordResetView.as_view(
            success_url=reverse_lazy("babybuddy:password_reset_done")
        ),
        name="password_reset",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            success_url=reverse_lazy("babybuddy:password_reset_complete")
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("", views.RootRouter.as_view(), name="root-router"),
    path("welcome/", views.Welcome.as_view(), name="welcome"),
    path("users/", views.UserList.as_view(), name="user-list"),
    path("users/add/", views.UserAdd.as_view(), name="user-add"),
    path("users/<int:pk>/edit/", views.UserUpdate.as_view(), name="user-update"),
    path("users/<int:pk>/unlock/", views.UserUnlock.as_view(), name="user-unlock"),
    path("users/<int:pk>/delete/", views.UserDelete.as_view(), name="user-delete"),
    path("user/password/", views.UserPassword.as_view(), name="user-password"),
    path("user/settings/", views.UserSettings.as_view(), name="user-settings"),
    path("user/add-device/", views.UserAddDevice.as_view(), name="user-add-device"),
    path("settings/", include("dbsettings.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("api.urls", namespace="api")),
    path("", include((app_patterns, "babybuddy"), namespace="babybuddy")),
    path("user/lang", include("django.conf.urls.i18n")),
    path("", include("core.urls", namespace="core")),
    path("", include("dashboard.urls", namespace="dashboard")),
    path("", include("reports.urls", namespace="reports")),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
