# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse

from django.views.generic import View
from django.views.generic.base import TemplateView, RedirectView

from .forms import UserForm, UserSettingsForm
from core.models import Child


class RootRouter(LoginRequiredMixin, RedirectView):
    """
    Redirects to the welcome page if no children are in the database, a child
    dashboard if only one child is in the database, and the dashboard page if
    more than one child is in the database.
    """
    def get_redirect_url(self, *args, **kwargs):
        children = Child.objects.count()
        if children == 0:
            self.url = reverse('welcome')
        elif children == 1:
            self.url = reverse(
                'dashboard-child', args={Child.objects.first().slug})
        else:
            self.url = reverse('dashboard')
        return super(RootRouter, self).get_redirect_url(self, *args, **kwargs)


class UserSettings(LoginRequiredMixin, View):
    """
    Handles both the User and Settings models.
    Based on this SO answer: https://stackoverflow.com/a/45056835.
    """
    form_user_class = UserForm
    form_settings_class = UserSettingsForm
    template_name = 'babybuddy/user_settings_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'form_user': self.form_user_class(instance=request.user),
            'form_settings': self.form_settings_class(
                instance=request.user.settings)
        })

    def post(self, request):
        form_user = self.form_user_class(
            instance=request.user,
            data=request.POST)
        form_settings = self.form_settings_class(
            instance=request.user.settings,
            data=request.POST)
        if form_user.is_valid() and form_settings.is_valid():
            user = form_user.save(commit=False)
            user_settings = form_settings.save(commit=False)
            user.settings = user_settings
            user.save()
            return redirect('user-settings')
        return render(request, self.template_name, {
            'user_form': form_user,
            'settings_form': form_settings
        })


class Welcome(LoginRequiredMixin, TemplateView):
    """
    Basic introduction to Baby Buddy (meant to be shown when no data is in the
    database).
    """
    template_name = 'babybuddy/welcome.html'
