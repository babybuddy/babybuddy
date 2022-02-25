# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LogoutView as LogoutViewBase
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseForbidden
from django.middleware.csrf import REASON_BAD_ORIGIN
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.text import format_lazy
from django.utils.translation import gettext as _, gettext_lazy
from django.views import csrf
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import View
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.i18n import set_language

from django_filters.views import FilterView

from babybuddy import forms
from babybuddy.mixins import LoginRequiredMixin, PermissionRequiredMixin, StaffOnlyMixin


def csrf_failure(request, reason=""):
    """
    Overrides the 403 CSRF failure template for bad origins in order to provide more
    userful information about how to resolve the issue.
    """

    if (
        "HTTP_ORIGIN" in request.META
        and reason == REASON_BAD_ORIGIN % request.META["HTTP_ORIGIN"]
    ):
        context = {
            "title": _("Forbidden"),
            "main": _("CSRF verification failed. Request aborted."),
            "reason": reason,
            "origin": request.META["HTTP_ORIGIN"],
        }
        template = loader.get_template("error/403_csrf_bad_origin.html")
        return HttpResponseForbidden(template.render(context), content_type="text/html")

    return csrf.csrf_failure(request, reason, "403_csrf.html")


class RootRouter(LoginRequiredMixin, RedirectView):
    """
    Redirects to the site dashboard.
    """

    def get_redirect_url(self, *args, **kwargs):
        self.url = reverse("dashboard:dashboard")
        return super(RootRouter, self).get_redirect_url(self, *args, **kwargs)


class BabyBuddyFilterView(FilterView):
    """
    Disables "strictness" for django-filter. It is unclear from the
    documentation exactly what this does...
    """

    # TODO Figure out the correct way to use this.
    strict = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        children = {o.child for o in context["object_list"] if hasattr(o, "child")}
        if len(children) == 1:
            context["unique_child"] = True
        return context


@method_decorator(csrf_protect, name="dispatch")
@method_decorator(never_cache, name="dispatch")
@method_decorator(require_POST, name="dispatch")
class LogoutView(LogoutViewBase):
    pass


class UserList(StaffOnlyMixin, BabyBuddyFilterView):
    model = User
    template_name = "babybuddy/user_list.html"
    ordering = "username"
    paginate_by = 10
    filterset_fields = ("username", "first_name", "last_name", "email")


class UserAdd(StaffOnlyMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = User
    template_name = "babybuddy/user_form.html"
    permission_required = ("admin.add_user",)
    form_class = forms.UserAddForm
    success_url = reverse_lazy("babybuddy:user-list")
    success_message = gettext_lazy("User %(username)s added!")


class UserUpdate(
    StaffOnlyMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = User
    template_name = "babybuddy/user_form.html"
    permission_required = ("admin.change_user",)
    form_class = forms.UserUpdateForm
    success_url = reverse_lazy("babybuddy:user-list")
    success_message = gettext_lazy("User %(username)s updated.")


class UserDelete(
    StaffOnlyMixin, PermissionRequiredMixin, DeleteView, SuccessMessageMixin
):
    model = User
    template_name = "babybuddy/user_confirm_delete.html"
    permission_required = ("admin.delete_user",)
    success_url = reverse_lazy("babybuddy:user-list")

    def get_success_message(self, cleaned_data):
        return format_lazy(gettext_lazy("User {user} deleted."), user=self.get_object())


class UserPassword(LoginRequiredMixin, View):
    """
    Handles user password changes.
    """

    form_class = forms.UserPasswordForm
    template_name = "babybuddy/user_password_form.html"

    def get(self, request):
        return render(
            request, self.template_name, {"form": self.form_class(request.user)}
        )

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _("Password updated."))
        return render(request, self.template_name, {"form": form})


class UserSettings(LoginRequiredMixin, View):
    """
    Handles both the User and Settings models.
    Based on this SO answer: https://stackoverflow.com/a/45056835.
    """

    form_user_class = forms.UserForm
    form_settings_class = forms.UserSettingsForm
    template_name = "babybuddy/user_settings_form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "form_user": self.form_user_class(instance=request.user),
                "form_settings": self.form_settings_class(
                    instance=request.user.settings
                ),
            },
        )

    def post(self, request):
        if request.POST.get("api_key_regenerate"):
            request.user.settings.api_key(reset=True)
            messages.success(request, _("User API key regenerated."))
            return redirect("babybuddy:user-settings")

        form_user = self.form_user_class(instance=request.user, data=request.POST)
        form_settings = self.form_settings_class(
            instance=request.user.settings, data=request.POST
        )
        if form_user.is_valid() and form_settings.is_valid():
            user = form_user.save(commit=False)
            user_settings = form_settings.save(commit=False)
            user.settings = user_settings
            user.save()
            translation.activate(user.settings.language)
            messages.success(request, _("Settings saved!"))
            translation.deactivate()
            return set_language(request)
        return render(
            request,
            self.template_name,
            {"user_form": form_user, "settings_form": form_settings},
        )


class Welcome(LoginRequiredMixin, TemplateView):
    """
    Basic introduction to Baby Buddy (meant to be shown when no data is in the
    database).
    """

    template_name = "babybuddy/welcome.html"
