# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .models import Child


class Index(TemplateView):
    template_name = 'core/index.html'


class ChildAdd(CreateView):
    model = Child
    fields = ['first_name', 'last_name', 'birth_date']
    success_url = '/'


class ChildUpdate(UpdateView):
    model = Child
    fields = ['first_name', 'last_name', 'birth_date']
    success_url = '/'


class ChildDelete(DeleteView):
    model = Child
