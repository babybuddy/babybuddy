# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django_filters.views import FilterView

from babybuddy import forms
from babybuddy.mixins import StaffOnlyMixin
from core import models


class RootRouter(LoginRequiredMixin, RedirectView):
    """
    Redirects to the welcome page if no children are in the database, a child
    dashboard if only one child is in the database, and the dashboard page if
    more than one child is in the database.
    """
    def get_redirect_url(self, *args, **kwargs):
        children = models.Child.objects.count()
        if children == 0:
            self.url = reverse('babybuddy:welcome')
        elif children == 1:
            self.url = reverse(
                'dashboard:dashboard-child',
                args={models.Child.objects.first().slug}
            )
        else:
            self.url = reverse('dashboard:dashboard')
        return super(RootRouter, self).get_redirect_url(self, *args, **kwargs)


class UserList(StaffOnlyMixin, FilterView):
    model = User
    template_name = 'babybuddy/user_list.html'
    ordering = 'username'
    paginate_by = 10
    filter_fields = ('username', 'first_name', 'last_name', 'email')


class UserAdd(StaffOnlyMixin, PermissionRequiredMixin, SuccessMessageMixin,
              CreateView):
    model = User
    template_name = 'babybuddy/user_form.html'
    permission_required = ('admin.add_user',)
    form_class = forms.UserAddForm
    success_url = reverse_lazy('babybuddy:user-list')
    success_message = 'User %(username)s added!'


class UserUpdate(StaffOnlyMixin, PermissionRequiredMixin, SuccessMessageMixin,
                 UpdateView):
    model = User
    template_name = 'babybuddy/user_form.html'
    permission_required = ('admin.change_user',)
    form_class = forms.UserUpdateForm
    success_url = reverse_lazy('babybuddy:user-list')
    success_message = 'User %(username)s updated.'


class UserDelete(StaffOnlyMixin, PermissionRequiredMixin,
                 DeleteView):
    model = User
    template_name = 'babybuddy/user_confirm_delete.html'
    permission_required = ('admin.delete_user',)
    success_url = reverse_lazy('babybuddy:user-list')

    def delete(self, request, *args, **kwargs):
        success_message = 'User {} deleted.'.format(self.get_object())
        messages.success(request, success_message)
        return super(UserDelete, self).delete(request, *args, **kwargs)


class UserPassword(LoginRequiredMixin, View):
    """
    Handles user password changes.
    """
    form_class = forms.UserPasswordForm
    template_name = 'babybuddy/user_password_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'form': self.form_class(request.user)
        })

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated.')
        return render(request, self.template_name, {'form': form})


class UserResetAPIKey(LoginRequiredMixin, View):
    """
    Resets the API key of the logged in user.
    """
    def get(self, request):
        request.user.settings.api_key(reset=True)
        messages.success(request, 'User API key regenerated.')
        return redirect('babybuddy:user-settings')


class UserSettings(LoginRequiredMixin, View):
    """
    Handles both the User and Settings models.
    Based on this SO answer: https://stackoverflow.com/a/45056835.
    """
    form_user_class = forms.UserForm
    form_settings_class = forms.UserSettingsForm
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
            messages.success(request, 'Settings saved!')
            return redirect('babybuddy:user-settings')
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
