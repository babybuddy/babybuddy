# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.urls import reverse
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.detail import DetailView

from core.models import Child


class DashboardRedirect(LoginRequiredMixin, RedirectView):
    # Show the overall dashboard or a child dashboard if one Child instance.
    def get(self, request, *args, **kwargs):
        if Child.objects.count() == 1:
            child_instance = Child.objects.first()
            self.url = reverse('dashboard-child', args={child_instance.slug})
        else:
            self.url = reverse('dashboard')
        return super(DashboardRedirect, self).get(request, *args, **kwargs)


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'


class ChildDashboard(PermissionRequiredMixin, DetailView):
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'dashboard/child.html'
