# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from .models import Child


class Index(TemplateView):
    template_name = 'core/index.html'


class ChildList(ListView):
    model = Child


class ChildAdd(CreateView):
    model = Child
    fields = ['first_name', 'last_name', 'birth_date']
    success_url = '/children'


class ChildUpdate(UpdateView):
    model = Child
    fields = ['first_name', 'last_name', 'birth_date']
    success_url = '/children'


class ChildDelete(DeleteView):
    model = Child
