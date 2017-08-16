# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from .models import Child, DiaperChange, Feeding, Note, Sleep, TummyTime


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
    success_url = '/children'


class DiaperChangeList(ListView):
    model = DiaperChange


class DiaperChangeAdd(CreateView):
    model = DiaperChange
    fields = ['child', 'time', 'wet', 'solid', 'color']
    success_url = '/changes'


class DiaperChangeUpdate(UpdateView):
    model = DiaperChange
    fields = ['child', 'time', 'wet', 'solid', 'color']
    success_url = '/changes'


class DiaperChangeDelete(DeleteView):
    model = DiaperChange
    success_url = '/changes'


class FeedingList(ListView):
    model = Feeding


class FeedingAdd(CreateView):
    model = Feeding
    fields = ['child', 'start', 'end', 'type', 'method']
    success_url = '/feedings'


class FeedingUpdate(UpdateView):
    model = Feeding
    fields = ['child', 'start', 'end', 'type', 'method']
    success_url = '/feedings'


class FeedingDelete(DeleteView):
    model = Feeding
    success_url = '/feedings'


class NoteList(ListView):
    model = Note


class NoteAdd(CreateView):
    model = Note
    fields = ['child', 'note']
    success_url = '/notes'


class NoteUpdate(UpdateView):
    model = Note
    fields = ['child', 'note']
    success_url = '/notes'


class NoteDelete(DeleteView):
    model = Note
    success_url = '/notes'


class SleepList(ListView):
    model = Sleep


class SleepAdd(CreateView):
    model = Sleep
    fields = ['child', 'start', 'end']
    success_url = '/sleep'


class SleepUpdate(UpdateView):
    model = Sleep
    fields = ['child', 'start', 'end']
    success_url = '/sleep'


class SleepDelete(DeleteView):
    model = Sleep
    success_url = '/sleep'


class TummyTimeList(ListView):
    model = TummyTime


class TummyTimeAdd(CreateView):
    model = TummyTime
    fields = ['child', 'start', 'end', 'milestone']
    success_url = '/tummy-time'


class TummyTimeUpdate(UpdateView):
    model = TummyTime
    fields = ['child', 'start', 'end', 'milestone']
    success_url = '/tummy-time'


class TummyTimeDelete(DeleteView):
    model = TummyTime
    success_url = '/tummy-time'
