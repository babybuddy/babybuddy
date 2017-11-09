# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic.base import TemplateView, RedirectView

from core.models import Child


class RootRouter(LoginRequiredMixin, RedirectView):
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


class Welcome(LoginRequiredMixin, TemplateView):
    template_name = 'babybuddy/welcome.html'
