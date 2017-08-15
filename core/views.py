# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .models import Baby


class Index(TemplateView):
    template_name = 'core/index.html'


class BabyAdd(CreateView):
    model = Baby
    fields = ['first_name', 'last_name', 'birth_date']
    success_url = '/'


class BabyUpdate(UpdateView):
    model = Baby
    fields = ['first_name', 'last_name', 'birth_date']
    success_url = '/'


class BabyDelete(DeleteView):
    model = Baby
