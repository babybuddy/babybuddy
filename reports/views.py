# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.detail import DetailView

from core.models import Child


class SleepReport(PermissionRequiredMixin, DetailView):
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep.html'
