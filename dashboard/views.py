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
        children = Child.objects.count()
        if children == 0:
            # TODO: Create some sort of welcome page.
            self.url = reverse('child-add')
        elif children == 1:
            child_instance = Child.objects.first()
            self.url = reverse('dashboard-child', args={child_instance.slug})
        else:
            self.url = reverse('dashboard')
        return super(DashboardRedirect, self).get(request, *args, **kwargs)


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        context['objects'] = Child.objects.all().order_by('last_name')
        return context


class ChildDashboard(PermissionRequiredMixin, DetailView):
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'dashboard/child.html'
