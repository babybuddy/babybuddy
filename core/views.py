# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import resolve
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from .models import Child, DiaperChange, Feeding, Note, Sleep, Timer, TummyTime
from .forms import (ChildForm, DiaperChangeForm, FeedingForm, SleepForm,
                    TimerForm, TummyTimeForm)


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'core/index.html'


class ChildList(LoginRequiredMixin, ListView):
    model = Child


class ChildAdd(LoginRequiredMixin, CreateView):
    model = Child
    form_class = ChildForm
    success_url = '/children'


class ChildUpdate(LoginRequiredMixin, UpdateView):
    model = Child
    form_class = ChildForm
    success_url = '/children'


class ChildDelete(LoginRequiredMixin, DeleteView):
    model = Child
    success_url = '/children'


class DiaperChangeList(LoginRequiredMixin, ListView):
    model = DiaperChange


class DiaperChangeAdd(LoginRequiredMixin, CreateView):
    model = DiaperChange
    form_class = DiaperChangeForm
    success_url = '/changes'


class DiaperChangeUpdate(LoginRequiredMixin, UpdateView):
    model = DiaperChange
    form_class = DiaperChangeForm
    success_url = '/changes'


class DiaperChangeDelete(LoginRequiredMixin, DeleteView):
    model = DiaperChange
    success_url = '/changes'


class FeedingList(LoginRequiredMixin, ListView):
    model = Feeding


class FeedingAdd(LoginRequiredMixin, CreateView):
    model = Feeding
    form_class = FeedingForm
    success_url = '/feedings'


class FeedingUpdate(LoginRequiredMixin, UpdateView):
    model = Feeding
    form_class = FeedingForm
    success_url = '/feedings'


class FeedingDelete(LoginRequiredMixin, DeleteView):
    model = Feeding
    success_url = '/feedings'


class NoteList(LoginRequiredMixin, ListView):
    model = Note


class NoteAdd(LoginRequiredMixin, CreateView):
    model = Note
    fields = ['child', 'note']
    success_url = '/notes'


class NoteUpdate(LoginRequiredMixin, UpdateView):
    model = Note
    fields = ['child', 'note']
    success_url = '/notes'


class NoteDelete(LoginRequiredMixin, DeleteView):
    model = Note
    success_url = '/notes'


class SleepList(LoginRequiredMixin, ListView):
    model = Sleep


class SleepAdd(LoginRequiredMixin, CreateView):
    model = Sleep
    form_class = SleepForm
    success_url = '/sleep'


class SleepUpdate(LoginRequiredMixin, UpdateView):
    model = Sleep
    form_class = SleepForm
    success_url = '/sleep'


class SleepDelete(LoginRequiredMixin, DeleteView):
    model = Sleep
    success_url = '/sleep'


class TimerAdd(LoginRequiredMixin, CreateView):
    model = Timer
    form_class = TimerForm

    def get_success_url(self):
        if resolve(self.request.POST['success_url']).url_name:
            url = self.request.POST['success_url']
        else:
            url = '/'
        return url


class TummyTimeList(LoginRequiredMixin, ListView):
    model = TummyTime


class TummyTimeAdd(LoginRequiredMixin, CreateView):
    model = TummyTime
    form_class = TummyTimeForm
    success_url = '/tummy-time'


class TummyTimeUpdate(LoginRequiredMixin, UpdateView):
    model = TummyTime
    form_class = TummyTimeForm
    success_url = '/tummy-time'


class TummyTimeDelete(LoginRequiredMixin, DeleteView):
    model = TummyTime
    success_url = '/tummy-time'
