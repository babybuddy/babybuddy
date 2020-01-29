# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from babybuddy.mixins import PermissionRequired403Mixin
from babybuddy.views import BabyBuddyFilterView
from core import forms, models, timeline


class CoreAddView(PermissionRequired403Mixin, SuccessMessageMixin, CreateView):
    def get_success_message(self, cleaned_data):
        cleaned_data['model'] = self.model._meta.verbose_name.title()
        if 'child' in cleaned_data:
            self.success_message = _('%(model)s entry for %(child)s added!')
        else:
            self.success_message = _('%(model)s entry added!')
        return self.success_message % cleaned_data

    def get_form_kwargs(self):
        """
        Check for and add "child" and "timer" from request query parameters.
          - "child" may provide a slug for a Child instance.
          - "timer" may provided an ID for a Timer instance.

        These arguments are used in some add views to pre-fill initial data in
        the form fields.

        :return: Updated keyword arguments.
        """
        kwargs = super(CoreAddView, self).get_form_kwargs()
        kwargs.update({'child': self.request.GET.get('child', None)})
        kwargs.update({'timer': self.request.GET.get('timer', None)})
        return kwargs


class CoreUpdateView(PermissionRequired403Mixin, SuccessMessageMixin,
                     UpdateView):
    def get_success_message(self, cleaned_data):
        cleaned_data['model'] = self.model._meta.verbose_name.title()
        if 'child' in cleaned_data:
            self.success_message = _('%(model)s entry for %(child)s updated.')
        else:
            self.success_message = _('%(model)s entry updated.')
        return self.success_message % cleaned_data


class CoreDeleteView(PermissionRequired403Mixin, DeleteView):
    """
    SuccessMessageMixin is not compatible DeleteView.
    See: https://code.djangoproject.com/ticket/21936
    """
    def delete(self, request, *args, **kwargs):
        success_message = _('%(model)s entry deleted.') % {
            'model': self.model._meta.verbose_name.title()
        }
        messages.success(request, success_message)
        return super(CoreDeleteView, self).delete(request, *args, **kwargs)


class ChildList(PermissionRequired403Mixin, BabyBuddyFilterView):
    model = models.Child
    template_name = 'core/child_list.html'
    permission_required = ('core.view_child',)
    paginate_by = 10
    filterset_fields = ('first_name', 'last_name')


class ChildAdd(CoreAddView):
    model = models.Child
    permission_required = ('core.add_child',)
    form_class = forms.ChildForm
    success_url = reverse_lazy('core:child-list')
    success_message = _('%(first_name)s %(last_name)s added!')


class ChildDetail(PermissionRequired403Mixin, DetailView):
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
    success_url = reverse_lazy('core:child-list')


class ChildDelete(CoreUpdateView):
    model = models.Child
    form_class = forms.ChildDeleteForm
    template_name = 'core/child_confirm_delete.html'
    permission_required = ('core.delete_child',)
    success_url = reverse_lazy('core:child-list')


class DiaperChangeList(PermissionRequired403Mixin, BabyBuddyFilterView):
    model = models.DiaperChange
    template_name = 'core/diaperchange_list.html'
    permission_required = ('core.view_diaperchange',)
    paginate_by = 10
    filterset_fields = ('child', 'wet', 'solid', 'color')


class DiaperChangeAdd(CoreAddView):
    model = models.DiaperChange
    permission_required = ('core.add_diaperchange',)
    form_class = forms.DiaperChangeForm
    success_url = reverse_lazy('core:diaperchange-list')


class DiaperChangeUpdate(CoreUpdateView):
    model = models.DiaperChange
    permission_required = ('core.change_diaperchange',)
    form_class = forms.DiaperChangeForm
    success_url = reverse_lazy('core:diaperchange-list')


class DiaperChangeDelete(CoreDeleteView):
    model = models.DiaperChange
    permission_required = ('core.delete_diaperchange',)
    success_url = reverse_lazy('core:diaperchange-list')


class FeedingList(PermissionRequired403Mixin, BabyBuddyFilterView):
    model = models.Feeding
    template_name = 'core/feeding_list.html'
    permission_required = ('core.view_feeding',)
    paginate_by = 10
    filterset_fields = ('child', 'type', 'method')


class FeedingAdd(CoreAddView):
    model = models.Feeding
    permission_required = ('core.add_feeding',)
    form_class = forms.FeedingForm
    success_url = reverse_lazy('core:feeding-list')


class FeedingUpdate(CoreUpdateView):
    model = models.Feeding
    permission_required = ('core.change_feeding',)
    form_class = forms.FeedingForm
    success_url = reverse_lazy('core:feeding-list')


class FeedingDelete(CoreDeleteView):
    model = models.Feeding
    permission_required = ('core.delete_feeding',)
    success_url = reverse_lazy('core:feeding-list')


class NoteList(PermissionRequired403Mixin, BabyBuddyFilterView):
    model = models.Note
    template_name = 'core/note_list.html'
    permission_required = ('core.view_note',)
    paginate_by = 10
    filterset_fields = ('child',)


class NoteAdd(CoreAddView):
    model = models.Note
    permission_required = ('core.add_note',)
    form_class = forms.NoteForm
    success_url = reverse_lazy('core:note-list')


class NoteUpdate(CoreUpdateView):
    model = models.Note
    permission_required = ('core.change_note',)
    fields = ['child', 'note']
    success_url = reverse_lazy('core:note-list')


class NoteDelete(CoreDeleteView):
    model = models.Note
    permission_required = ('core.delete_note',)
    success_url = reverse_lazy('core:note-list')


class SleepList(PermissionRequired403Mixin, BabyBuddyFilterView):
    model = models.Sleep
    template_name = 'core/sleep_list.html'
    permission_required = ('core.view_sleep',)
    paginate_by = 10
    filterset_fields = ('child',)


class SleepAdd(CoreAddView):
    model = models.Sleep
    permission_required = ('core.add_sleep',)
    form_class = forms.SleepForm
    success_url = reverse_lazy('core:sleep-list')


class SleepUpdate(CoreUpdateView):
    model = models.Sleep
    permission_required = ('core.change_sleep',)
    form_class = forms.SleepForm
    success_url = reverse_lazy('core:sleep-list')


class SleepDelete(CoreDeleteView):
    model = models.Sleep
    permission_required = ('core.delete_sleep',)
    success_url = reverse_lazy('core:sleep-list')


class TemperatureList(PermissionRequired403Mixin, BabyBuddyFilterView):
    model = models.Temperature
    template_name = 'core/temperature_list.html'
    permission_required = ('core.view_temperature',)
    paginate_by = 10
    filterset_fields = ('child',)


class TemperatureAdd(CoreAddView):
    model = models.Temperature
    permission_required = ('core.add_temperature',)
    form_class = forms.TemperatureForm
    success_url = reverse_lazy('core:temperature-list')
    success_message = _('%(model)s reading added!')


class TemperatureUpdate(CoreUpdateView):
    model = models.Temperature
    permission_required = ('core.change_temperature',)
    fields = ['child', 'temperature', 'time']
    success_url = reverse_lazy('core:temperature-list')
    success_message = _('%(model)s reading for %(child)s updated.')


class TemperatureDelete(CoreDeleteView):
    model = models.Temperature
    permission_required = ('core.delete_temperature',)
    success_url = reverse_lazy('core:temperature-list')


class TimerList(PermissionRequired403Mixin, BabyBuddyFilterView):
    model = models.Timer
    template_name = 'core/timer_list.html'
    permission_required = ('core.view_timer',)
    paginate_by = 10
    filterset_fields = ('active', 'user')


class TimerDetail(PermissionRequired403Mixin, DetailView):
    model = models.Timer
    permission_required = ('core.view_timer',)


class TimerAdd(PermissionRequired403Mixin, CreateView):
    model = models.Timer
    permission_required = ('core.add_timer',)
    form_class = forms.TimerForm

    def get_form_kwargs(self):
        kwargs = super(TimerAdd, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_success_url(self):
        return reverse('core:timer-detail', kwargs={'pk': self.object.pk})


class TimerUpdate(CoreUpdateView):
    model = models.Timer
    permission_required = ('core.change_timer',)
    form_class = forms.TimerForm
    success_url = reverse_lazy('core:timer-list')

    def get_form_kwargs(self):
        kwargs = super(TimerUpdate, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_success_url(self):
        instance = self.get_object()
        return reverse('core:timer-detail', kwargs={'pk': instance.pk})


class TimerAddQuick(PermissionRequired403Mixin, RedirectView):
    permission_required = ('core.add_timer',)

    def get(self, request, *args, **kwargs):
        instance = models.Timer.objects.create(user=request.user)
        # Add child relationship if there is only Child instance.
        if models.Child.count() == 1:
            instance.child = models.Child.objects.first()
        instance.save()
        self.url = request.GET.get(
            'next', reverse('core:timer-detail', args={instance.id}))
        return super(TimerAddQuick, self).get(request, *args, **kwargs)


class TimerRestart(PermissionRequired403Mixin, RedirectView):
    permission_required = ('core.change_timer',)

    def get(self, request, *args, **kwargs):
        instance = models.Timer.objects.get(id=kwargs['pk'])
        instance.restart()
        messages.success(request, '{} restarted.'.format(instance))
        return super(TimerRestart, self).get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('core:timer-detail', kwargs={'pk': kwargs['pk']})


class TimerStop(PermissionRequired403Mixin, SuccessMessageMixin, RedirectView):
    permission_required = ('core.change_timer',)
    success_message = _('%(timer)s stopped.')

    def get(self, request, *args, **kwargs):
        instance = models.Timer.objects.get(id=kwargs['pk'])
        instance.stop()
        messages.success(request, '{} stopped.'.format(instance))
        return super(TimerStop, self).get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('core:timer-detail', kwargs={'pk': kwargs['pk']})


class TimerDelete(CoreDeleteView):
    model = models.Timer
    permission_required = ('core.delete_timer',)
    success_url = reverse_lazy('core:timer-list')


class TummyTimeList(PermissionRequired403Mixin, BabyBuddyFilterView):
    model = models.TummyTime
    template_name = 'core/tummytime_list.html'
    permission_required = ('core.view_tummytime',)
    paginate_by = 10
    filterset_fields = ('child',)


class TummyTimeAdd(CoreAddView):
    model = models.TummyTime
    permission_required = ('core.add_tummytime',)
    form_class = forms.TummyTimeForm
    success_url = reverse_lazy('core:tummytime-list')


class TummyTimeUpdate(CoreUpdateView):
    model = models.TummyTime
    permission_required = ('core.change_tummytime',)
    form_class = forms.TummyTimeForm
    success_url = reverse_lazy('core:tummytime-list')


class TummyTimeDelete(CoreDeleteView):
    model = models.TummyTime
    permission_required = ('core.delete_tummytime',)
    success_url = reverse_lazy('core:tummytime-list')


class WeightList(PermissionRequired403Mixin, BabyBuddyFilterView):
    model = models.Weight
    template_name = 'core/weight_list.html'
    permission_required = ('core.view_weight',)
    paginate_by = 10
    filterset_fields = ('child',)


class WeightAdd(CoreAddView):
    model = models.Weight
    permission_required = ('core.add_weight',)
    form_class = forms.WeightForm
    success_url = reverse_lazy('core:weight-list')


class WeightUpdate(CoreUpdateView):
    model = models.Weight
    permission_required = ('core.change_weight',)
    fields = ['child', 'weight', 'date']
    success_url = reverse_lazy('core:weight-list')


class WeightDelete(CoreDeleteView):
    model = models.Weight
    permission_required = ('core.delete_weight',)
    success_url = reverse_lazy('core:weight-list')
