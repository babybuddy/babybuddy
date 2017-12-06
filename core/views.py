# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils import timezone
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django_filters.views import FilterView

from core import forms, models, timeline


class CoreAddView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    def get_success_message(self, cleaned_data):
        cleaned_data['model'] = self.model._meta.verbose_name.title()
        if 'child' in cleaned_data:
            self.success_message = '%(model)s entry for %(child)s added!'
        else:
            self.success_message = '%(model)s entry added!'
        return self.success_message % cleaned_data


class CoreUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    def get_success_message(self, cleaned_data):
        cleaned_data['model'] = self.model._meta.verbose_name.title()
        if 'child' in cleaned_data:
            self.success_message = '%(model)s entry for %(child)s updated.'
        else:
            self.success_message = '%(model)s entry updated.'
        return self.success_message % cleaned_data


class CoreDeleteView(PermissionRequiredMixin, DeleteView):
    """
    SuccessMessageMixin is not compatible DeleteView.
    See: https://code.djangoproject.com/ticket/21936
    """
    def delete(self, request, *args, **kwargs):
        success_message = '{} entry deleted.'.format(
            self.model._meta.verbose_name.title())
        messages.success(request, success_message)
        return super(CoreDeleteView, self).delete(request, *args, **kwargs)


class ChildList(PermissionRequiredMixin, FilterView):
    model = models.Child
    template_name = 'core/child_list.html'
    permission_required = ('core.view_child',)
    paginate_by = 10
    filter_fields = ('first_name', 'last_name')


class ChildAdd(CoreAddView):
    model = models.Child
    permission_required = ('core.add_child',)
    form_class = forms.ChildForm
    success_url = '/children'
    success_message = '%(first_name)s %(last_name)s added!'


class ChildDetail(PermissionRequiredMixin, DetailView):
    model = models.Child
    permission_required = ('core.view_child',)

    def get_context_data(self, **kwargs):
        context = super(ChildDetail, self).get_context_data(**kwargs)
        date = self.request.GET.get('date', str(timezone.localdate()))
        date = timezone.datetime.strptime(date, '%Y-%m-%d')
        date = timezone.localtime(timezone.make_aware(date))
        context['timeline_objects'] = timeline.get_objects(self.object, date)
        context['date'] = date
        context['date_previous'] = date - timezone.timedelta(days=1)
        if date.date() < timezone.localdate():
            context['date_next'] = date + timezone.timedelta(days=1)
        return context


class ChildUpdate(CoreUpdateView):
    model = models.Child
    permission_required = ('core.change_child',)
    form_class = forms.ChildForm
    success_url = '/children'


class ChildDelete(CoreUpdateView):
    model = models.Child
    form_class = forms.ChildDeleteForm
    template_name = 'core/child_confirm_delete.html'
    permission_required = ('core.delete_child',)
    success_url = '/children'


class DiaperChangeList(PermissionRequiredMixin, FilterView):
    model = models.DiaperChange
    template_name = 'core/diaperchange_list.html'
    permission_required = ('core.view_diaperchange',)
    paginate_by = 10
    filter_fields = ('child', 'wet', 'solid', 'color')


class DiaperChangeAdd(CoreAddView):
    model = models.DiaperChange
    permission_required = ('core.add_diaperchange',)
    form_class = forms.DiaperChangeForm
    success_url = '/changes'


class DiaperChangeUpdate(CoreUpdateView):
    model = models.DiaperChange
    permission_required = ('core.change_diaperchange',)
    form_class = forms.DiaperChangeForm
    success_url = '/changes'


class DiaperChangeDelete(CoreDeleteView):
    model = models.DiaperChange
    permission_required = ('core.delete_diaperchange',)
    success_url = '/changes'


class FeedingList(PermissionRequiredMixin, FilterView):
    model = models.Feeding
    template_name = 'core/feeding_list.html'
    permission_required = ('core.view_feeding',)
    paginate_by = 10
    filter_fields = ('child', 'type', 'method')


class FeedingAdd(CoreAddView):
    model = models.Feeding
    permission_required = ('core.add_feeding',)
    form_class = forms.FeedingForm
    success_url = '/feedings'

    def get_form_kwargs(self):
        kwargs = super(FeedingAdd, self).get_form_kwargs()
        # Add timer to be used by FeedingForm.__init__
        kwargs.update({'timer': self.request.GET.get('timer', None)})
        return kwargs


class FeedingUpdate(CoreUpdateView):
    model = models.Feeding
    permission_required = ('core.change_feeding',)
    form_class = forms.FeedingForm
    success_url = '/feedings'


class FeedingDelete(CoreDeleteView):
    model = models.Feeding
    permission_required = ('core.delete_feeding',)
    success_url = '/feedings'


class NoteList(PermissionRequiredMixin, FilterView):
    model = models.Note
    template_name = 'core/note_list.html'
    permission_required = ('core.view_note',)
    paginate_by = 10
    filter_fields = ('child',)


class NoteAdd(CoreAddView):
    model = models.Note
    permission_required = ('core.add_note',)
    form_class = forms.NoteForm
    success_url = '/notes'


class NoteUpdate(CoreUpdateView):
    model = models.Note
    permission_required = ('core.change_note',)
    fields = ['child', 'note']
    success_url = '/notes'


class NoteDelete(CoreDeleteView):
    model = models.Note
    permission_required = ('core.delete_note',)
    success_url = '/notes'


class SleepList(PermissionRequiredMixin, FilterView):
    model = models.Sleep
    template_name = 'core/sleep_list.html'
    permission_required = ('core.view_sleep',)
    paginate_by = 10
    filter_fields = ('child',)


class SleepAdd(CoreAddView):
    model = models.Sleep
    permission_required = ('core.add_sleep',)
    form_class = forms.SleepForm
    success_url = '/sleep'

    def get_form_kwargs(self):
        kwargs = super(SleepAdd, self).get_form_kwargs()
        # Add timer to be used by SleepForm.__init__
        kwargs.update({'timer': self.request.GET.get('timer', None)})
        return kwargs


class SleepUpdate(CoreUpdateView):
    model = models.Sleep
    permission_required = ('core.change_sleep',)
    form_class = forms.SleepForm
    success_url = '/sleep'


class SleepDelete(CoreDeleteView):
    model = models.Sleep
    permission_required = ('core.delete_sleep',)
    success_url = '/sleep'


class TimerList(PermissionRequiredMixin, FilterView):
    model = models.Timer
    template_name = 'core/timer_list.html'
    permission_required = ('core.view_timer',)
    paginate_by = 10
    filter_fields = ('active', 'user')


class TimerDetail(PermissionRequiredMixin, DetailView):
    model = models.Timer
    permission_required = ('core.view_timer',)


class TimerAdd(CoreAddView):
    model = models.Timer
    permission_required = ('core.add_timer',)
    form_class = forms.TimerForm
    success_url = '/timers'

    def get_form_kwargs(self):
        kwargs = super(TimerAdd, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


class TimerUpdate(CoreUpdateView):
    model = models.Timer
    permission_required = ('core.change_timer',)
    form_class = forms.TimerForm
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
        instance = models.Timer.objects.create(user=request.user)
        instance.save()
        messages.success(request, '{} started!'.format(instance))
        self.url = request.GET.get(
            'next', reverse('core:timer-detail', args={instance.id}))
        return super(TimerAddQuick, self).get(request, *args, **kwargs)


class TimerRestart(PermissionRequiredMixin, RedirectView):
    permission_required = ('core.change_timer',)

    def get(self, request, *args, **kwargs):
        instance = models.Timer.objects.get(id=kwargs['pk'])
        instance.restart()
        messages.success(request, '{} restarted.'.format(instance))
        return super(TimerRestart, self).get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return '/timer/{}'.format(kwargs['pk'])


class TimerStop(PermissionRequiredMixin, SuccessMessageMixin, RedirectView):
    permission_required = ('core.change_timer',)
    success_message = '%(timer)s stopped.'

    def get(self, request, *args, **kwargs):
        instance = models.Timer.objects.get(id=kwargs['pk'])
        instance.stop()
        messages.success(request, '{} stopped.'.format(instance))
        return super(TimerStop, self).get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return '/timer/{}'.format(kwargs['pk'])


class TimerDelete(CoreDeleteView):
    model = models.Timer
    permission_required = ('core.delete_timer',)
    success_url = '/timers'


class TummyTimeList(PermissionRequiredMixin, FilterView):
    model = models.TummyTime
    template_name = 'core/tummytime_list.html'
    permission_required = ('core.view_tummytime',)
    paginate_by = 10
    filter_fields = ('child',)


class TummyTimeAdd(CoreAddView):
    model = models.TummyTime
    permission_required = ('core.add_tummytime',)
    form_class = forms.TummyTimeForm
    success_url = '/tummy-time'

    def get_form_kwargs(self):
        kwargs = super(TummyTimeAdd, self).get_form_kwargs()
        # Add timer to be used by TummyTimeForm.__init__
        kwargs.update({'timer': self.request.GET.get('timer', None)})
        return kwargs


class TummyTimeUpdate(CoreUpdateView):
    model = models.TummyTime
    permission_required = ('core.change_tummytime',)
    form_class = forms.TummyTimeForm
    success_url = '/tummy-time'


class TummyTimeDelete(CoreDeleteView):
    model = models.TummyTime
    permission_required = ('core.delete_tummytime',)
    success_url = '/tummy-time'


class WeightList(PermissionRequiredMixin, FilterView):
    model = models.Weight
    template_name = 'core/weight_list.html'
    permission_required = ('core.view_weight',)
    paginate_by = 10
    filter_fields = ('child',)


class WeightAdd(CoreAddView):
    model = models.Weight
    permission_required = ('core.add_weight',)
    form_class = forms.WeightForm
    success_url = '/weight'


class WeightUpdate(CoreUpdateView):
    model = models.Weight
    permission_required = ('core.change_weight',)
    fields = ['child', 'weight', 'date']
    success_url = '/weight'


class WeightDelete(CoreDeleteView):
    model = models.Weight
    permission_required = ('core.delete_weight',)
    success_url = '/weight'
