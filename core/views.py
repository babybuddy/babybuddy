# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from .models import Child, DiaperChange, Feeding, Note, Sleep, Timer, TummyTime
from .forms import (ChildForm, DiaperChangeForm, FeedingForm, SleepForm,
                    TimerForm, TummyTimeForm)


class ChildList(PermissionRequiredMixin, ListView):
    model = Child
    permission_required = ('core.view_child',)
    paginate_by = 10


class ChildAdd(PermissionRequiredMixin, CreateView):
    model = Child
    permission_required = ('core.add_child',)
    form_class = ChildForm
    success_url = '/children'


class ChildDetail(PermissionRequiredMixin, DetailView):
    model = Child
    permission_required = ('core.view_child',)


class ChildUpdate(PermissionRequiredMixin, UpdateView):
    model = Child
    permission_required = ('core.change_child',)
    form_class = ChildForm
    success_url = '/children'


class ChildDelete(PermissionRequiredMixin, DeleteView):
    model = Child
    permission_required = ('core.delete_child',)
    success_url = '/children'


class DiaperChangeList(PermissionRequiredMixin, ListView):
    model = DiaperChange
    permission_required = ('core.view_diaperchange',)
    paginate_by = 10


class DiaperChangeAdd(PermissionRequiredMixin, CreateView):
    model = DiaperChange
    permission_required = ('core.add_diaperchange',)
    form_class = DiaperChangeForm
    success_url = '/changes'


class DiaperChangeUpdate(PermissionRequiredMixin, UpdateView):
    model = DiaperChange
    permission_required = ('core.change_diaperchange',)
    form_class = DiaperChangeForm
    success_url = '/changes'


class DiaperChangeDelete(PermissionRequiredMixin, DeleteView):
    model = DiaperChange
    permission_required = ('core.delete_diaperchange',)
    success_url = '/changes'


class FeedingList(PermissionRequiredMixin, ListView):
    model = Feeding
    permission_required = ('core.view_feeding',)
    paginate_by = 10


class FeedingAdd(PermissionRequiredMixin, CreateView):
    model = Feeding
    permission_required = ('core.add_feeding',)
    form_class = FeedingForm
    success_url = '/feedings'

    def get_form_kwargs(self):
        kwargs = super(FeedingAdd, self).get_form_kwargs()
        # Add timer to be used by FeedingForm.__init__
        kwargs.update({'timer': self.request.GET.get('timer', None)})
        return kwargs


class FeedingUpdate(PermissionRequiredMixin, UpdateView):
    model = Feeding
    permission_required = ('core.change_feeding',)
    form_class = FeedingForm
    success_url = '/feedings'


class FeedingDelete(PermissionRequiredMixin, DeleteView):
    model = Feeding
    permission_required = ('core.delete_feeding',)
    success_url = '/feedings'


class NoteList(PermissionRequiredMixin, ListView):
    model = Note
    permission_required = ('core.view_note',)
    paginate_by = 10


class NoteAdd(PermissionRequiredMixin, CreateView):
    model = Note
    permission_required = ('core.add_note',)
    fields = ['child', 'note']
    success_url = '/notes'


class NoteUpdate(PermissionRequiredMixin, UpdateView):
    model = Note
    permission_required = ('core.change_note',)
    fields = ['child', 'note']
    success_url = '/notes'


class NoteDelete(PermissionRequiredMixin, DeleteView):
    model = Note
    permission_required = ('core.delete_note',)
    success_url = '/notes'


class SleepList(PermissionRequiredMixin, ListView):
    model = Sleep
    permission_required = ('core.view_sleep',)
    paginate_by = 10


class SleepAdd(PermissionRequiredMixin, CreateView):
    model = Sleep
    permission_required = ('core.add_sleep',)
    form_class = SleepForm
    success_url = '/sleep'

    def get_form_kwargs(self):
        kwargs = super(SleepAdd, self).get_form_kwargs()
        # Add timer to be used by SleepForm.__init__
        kwargs.update({'timer': self.request.GET.get('timer', None)})
        return kwargs


class SleepUpdate(PermissionRequiredMixin, UpdateView):
    model = Sleep
    permission_required = ('core.change_sleep',)
    form_class = SleepForm
    success_url = '/sleep'


class SleepDelete(PermissionRequiredMixin, DeleteView):
    model = Sleep
    permission_required = ('core.delete_sleep',)
    success_url = '/sleep'


class TimerList(PermissionRequiredMixin, ListView):
    model = Timer
    permission_required = ('core.view_timer',)
    paginate_by = 10


class TimerDetail(PermissionRequiredMixin, DetailView):
    model = Timer
    permission_required = ('core.view_timer',)


class TimerAdd(PermissionRequiredMixin, CreateView):
    model = Timer
    permission_required = ('core.add_timer',)
    form_class = TimerForm
    success_url = '/timers'

    def get_form_kwargs(self):
        kwargs = super(TimerAdd, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


class TimerUpdate(PermissionRequiredMixin, UpdateView):
    model = Timer
    permission_required = ('core.change_timer',)
    form_class = TimerForm
    success_url = '/timers'

    def get_form_kwargs(self):
        kwargs = super(TimerUpdate, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_success_url(self):
        instance = self.get_object()
        return '/timer/{}/'.format(instance.id)


class TimerAddQuick(PermissionRequiredMixin, RedirectView):
    permission_required = ('core.add_timer',)

    def get(self, request, *args, **kwargs):
        instance = Timer.objects.create(user=request.user)
        instance.save()
        self.url = request.GET.get(
            'next', reverse('timer-detail', args={instance.id}))
        return super(TimerAddQuick, self).get(request, *args, **kwargs)


class TimerRestart(PermissionRequiredMixin, RedirectView):
    permission_required = ('core.change_timer',)

    def get(self, request, *args, **kwargs):
        instance = Timer.objects.get(id=kwargs['pk'])
        instance.restart()
        return super(TimerRestart, self).get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return '/timer/{}'.format(kwargs['pk'])


class TimerStop(PermissionRequiredMixin, RedirectView):
    permission_required = ('core.change_timer',)

    def get(self, request, *args, **kwargs):
        instance = Timer.objects.get(id=kwargs['pk'])
        instance.stop()
        return super(TimerStop, self).get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return '/timer/{}'.format(kwargs['pk'])


class TimerDelete(PermissionRequiredMixin, DeleteView):
    model = Timer
    permission_required = ('core.delete_timer',)
    success_url = '/'


class TummyTimeList(PermissionRequiredMixin, ListView):
    model = TummyTime
    permission_required = ('core.view_tummytime',)
    paginate_by = 10


class TummyTimeAdd(PermissionRequiredMixin, CreateView):
    model = TummyTime
    permission_required = ('core.add_tummytime',)
    form_class = TummyTimeForm
    success_url = '/tummy-time'

    def get_form_kwargs(self):
        kwargs = super(TummyTimeAdd, self).get_form_kwargs()
        # Add timer to be used by TummyTimeForm.__init__
        kwargs.update({'timer': self.request.GET.get('timer', None)})
        return kwargs


class TummyTimeUpdate(PermissionRequiredMixin, UpdateView):
    model = TummyTime
    permission_required = ('core.change_tummytime',)
    form_class = TummyTimeForm
    success_url = '/tummy-time'


class TummyTimeDelete(PermissionRequiredMixin, DeleteView):
    model = TummyTime
    permission_required = ('core.delete_tummytime',)
    success_url = '/tummy-time'
