# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.generic.base import RedirectView, TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.list import ListView

from babybuddy.mixins import LoginRequiredMixin, PermissionRequiredMixin
from babybuddy.views import BabyBuddyFilterView, BabyBuddyPaginatedView
from core import filters, forms, models, timeline


def _prepare_timeline_context_data(context, date, child=None):
    date = timezone.datetime.strptime(date, "%Y-%m-%d")
    date = timezone.localtime(timezone.make_aware(date))
    context["timeline_objects"] = timeline.get_objects(date, child)
    context["date"] = date
    context["date_previous"] = date - timezone.timedelta(days=1)
    if date.date() < timezone.localdate():
        context["date_next"] = date + timezone.timedelta(days=1)
    pass


class CoreAddView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    def get_success_message(self, cleaned_data):
        cleaned_data["model"] = self.model._meta.verbose_name.title()
        if "child" in cleaned_data:
            self.success_message = _("%(model)s entry for %(child)s added!")
        else:
            self.success_message = _("%(model)s entry added!")
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
        for parameter in ["child", "timer", "timer_name"]:
            value = self.request.GET.get(parameter, None)
            if value:
                kwargs.update({parameter: value})
        return kwargs


class CoreUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    def get_success_message(self, cleaned_data):
        cleaned_data["model"] = self.model._meta.verbose_name.title()
        if cleaned_data.get("child"):
            self.success_message = _("%(model)s entry for %(child)s updated.")
        else:
            self.success_message = _("%(model)s entry updated.")
        return self.success_message % cleaned_data


class CoreDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    def get_success_message(self, cleaned_data):
        return _("%(model)s entry deleted.") % {
            "model": self.model._meta.verbose_name.title()
        }


class BMIList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.BMI
    template_name = "core/bmi_list.html"
    permission_required = ("core.view_bmi",)
    filterset_class = filters.BMIFilter


class BMIAdd(CoreAddView):
    model = models.BMI
    permission_required = ("core.add_bmi",)
    form_class = forms.BMIForm
    success_url = reverse_lazy("core:bmi-list")


class BMIUpdate(CoreUpdateView):
    model = models.BMI
    permission_required = ("core.change_bmi",)
    form_class = forms.BMIForm
    success_url = reverse_lazy("core:bmi-list")


class BMIDelete(CoreDeleteView):
    model = models.BMI
    permission_required = ("core.delete_bmi",)
    success_url = reverse_lazy("core:bmi-list")


class ChildList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Child
    template_name = "core/child_list.html"
    permission_required = ("core.view_child",)
    filterset_fields = ("first_name", "last_name")


class ChildAdd(CoreAddView):
    model = models.Child
    permission_required = ("core.add_child",)
    form_class = forms.ChildForm
    success_url = reverse_lazy("core:child-list")
    success_message = _("%(first_name)s %(last_name)s added!")


class ChildDetail(PermissionRequiredMixin, DetailView):
    model = models.Child
    permission_required = ("core.view_child",)

    def get_context_data(self, **kwargs):
        context = super(ChildDetail, self).get_context_data(**kwargs)
        date = self.request.GET.get("date", str(timezone.localdate()))
        _prepare_timeline_context_data(context, date, self.object)
        return context


class ChildUpdate(CoreUpdateView):
    model = models.Child
    permission_required = ("core.change_child",)
    form_class = forms.ChildForm
    success_url = reverse_lazy("core:child-list")


class ChildDelete(CoreUpdateView):
    model = models.Child
    form_class = forms.ChildDeleteForm
    template_name = "core/child_confirm_delete.html"
    permission_required = ("core.delete_child",)
    success_url = reverse_lazy("core:child-list")

    def get_success_message(self, cleaned_data):
        """This class cannot use `CoreDeleteView` because of the confirmation
        step required so the success message must be overridden."""
        success_message = _("%(model)s entry deleted.") % {
            "model": self.model._meta.verbose_name.title()
        }
        return success_message % cleaned_data


class DiaperChangeList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.DiaperChange
    template_name = "core/diaperchange_list.html"
    permission_required = ("core.view_diaperchange",)
    filterset_class = filters.DiaperChangeFilter


class DiaperChangeAdd(CoreAddView):
    model = models.DiaperChange
    permission_required = ("core.add_diaperchange",)
    form_class = forms.DiaperChangeForm
    success_url = reverse_lazy("core:diaperchange-list")


class DiaperChangeUpdate(CoreUpdateView):
    model = models.DiaperChange
    permission_required = ("core.change_diaperchange",)
    form_class = forms.DiaperChangeForm
    success_url = reverse_lazy("core:diaperchange-list")


class DiaperChangeDelete(CoreDeleteView):
    model = models.DiaperChange
    permission_required = ("core.delete_diaperchange",)
    success_url = reverse_lazy("core:diaperchange-list")


class FeedingList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Feeding
    template_name = "core/feeding_list.html"
    permission_required = ("core.view_feeding",)
    filterset_class = filters.FeedingFilter


class FeedingAdd(CoreAddView):
    model = models.Feeding
    permission_required = ("core.add_feeding",)
    form_class = forms.FeedingForm
    success_url = reverse_lazy("core:feeding-list")


class BottleFeedingAdd(CoreAddView):
    model = models.Feeding
    permission_required = ("core.add_feeding",)
    form_class = forms.BottleFeedingForm
    success_url = reverse_lazy("core:feeding-list")


class BreastFeedingAdd(CoreAddView):
    model = models.Feeding
    permission_required = ("core.add_feeding",)
    form_class = forms.BreastFeedingForm
    success_url = reverse_lazy("core:feeding-list")


class SolidFeedingAdd(CoreAddView):
    model = models.Feeding
    permission_required = ("core.add_feeding",)
    form_class = forms.SolidFeedingForm
    success_url = reverse_lazy("core:feeding-list")


class FeedingUpdate(CoreUpdateView):
    model = models.Feeding
    permission_required = ("core.change_feeding",)
    success_url = reverse_lazy("core:feeding-list")

    def get_form_class(self):
        instance = self.get_object()
        method = instance.method
        feeding_type = instance.type

        if feeding_type == "solid food":
            return forms.SolidFeedingForm
        elif method in ("left breast", "right breast", "both breasts"):
            return forms.BreastFeedingForm
        elif method == "bottle":
            return forms.BottleFeedingForm
        else:
            # Fallback: full form for tube/cup/finger/syringe or unknown
            return forms.FeedingForm


class FeedingDelete(CoreDeleteView):
    model = models.Feeding
    permission_required = ("core.delete_feeding",)
    success_url = reverse_lazy("core:feeding-list")


class HeadCircumferenceList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.HeadCircumference
    template_name = "core/head_circumference_list.html"
    permission_required = ("core.view_head_circumference",)
    filterset_class = filters.HeadCircumferenceFilter


class HeadCircumferenceAdd(CoreAddView):
    model = models.HeadCircumference
    template_name = "core/head_circumference_form.html"
    permission_required = ("core.add_head_circumference",)
    form_class = forms.HeadCircumferenceForm
    success_url = reverse_lazy("core:head-circumference-list")


class HeadCircumferenceUpdate(CoreUpdateView):
    model = models.HeadCircumference
    template_name = "core/head_circumference_form.html"
    permission_required = ("core.change_head_circumference",)
    form_class = forms.HeadCircumferenceForm
    success_url = reverse_lazy("core:head-circumference-list")


class HeadCircumferenceDelete(CoreDeleteView):
    model = models.HeadCircumference
    template_name = "core/head_circumference_confirm_delete.html"
    permission_required = ("core.delete_head_circumference",)
    success_url = reverse_lazy("core:head-circumference-list")


class HeightList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Height
    template_name = "core/height_list.html"
    permission_required = ("core.view_height",)
    filterset_class = filters.HeightFilter


class HeightAdd(CoreAddView):
    model = models.Height
    permission_required = ("core.add_height",)
    form_class = forms.HeightForm
    success_url = reverse_lazy("core:height-list")


class HeightUpdate(CoreUpdateView):
    model = models.Height
    permission_required = ("core.change_height",)
    form_class = forms.HeightForm
    success_url = reverse_lazy("core:height-list")


class HeightDelete(CoreDeleteView):
    model = models.Height
    permission_required = ("core.delete_height",)
    success_url = reverse_lazy("core:height-list")


class MedicationList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.Medication
    template_name = "core/medication_list.html"
    permission_required = ("core.view_medication",)
    filterset_class = filters.MedicationFilter


class MedicationAdd(CoreAddView):
    model = models.Medication
    permission_required = ("core.add_medication",)
    form_class = forms.MedicationForm
    success_url = reverse_lazy("core:medication-list")

    def get_initial(self):
        initial = super().get_initial()
        visit_id = self.request.GET.get("visit")
        if visit_id:
            try:
                visit = models.DoctorVisit.objects.get(pk=visit_id)
                initial["doctor_visit"] = visit
                initial["time"] = visit.date_time
                initial["child"] = visit.child
            except models.DoctorVisit.DoesNotExist:
                pass
        return initial


class MedicationUpdate(CoreUpdateView):
    model = models.Medication
    permission_required = ("core.change_medication",)
    form_class = forms.MedicationForm
    success_url = reverse_lazy("core:medication-list")


class MedicationDelete(CoreDeleteView):
    model = models.Medication
    permission_required = ("core.delete_medication",)
    success_url = reverse_lazy("core:medication-list")


class NoteList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Note
    template_name = "core/note_list.html"
    permission_required = ("core.view_note",)
    filterset_class = filters.NoteFilter


class NoteAdd(CoreAddView):
    model = models.Note
    permission_required = ("core.add_note",)
    form_class = forms.NoteForm
    success_url = reverse_lazy("core:note-list")


class NoteUpdate(CoreUpdateView):
    model = models.Note
    permission_required = ("core.change_note",)
    form_class = forms.NoteForm
    success_url = reverse_lazy("core:note-list")


class NoteDelete(CoreDeleteView):
    model = models.Note
    permission_required = ("core.delete_note",)
    success_url = reverse_lazy("core:note-list")


class PumpingList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Pumping
    template_name = "core/pumping_list.html"
    permission_required = ("core.view_pumping",)
    filterset_class = filters.PumpingFilter


class PumpingAdd(CoreAddView):
    model = models.Pumping
    permission_required = ("core.add_pumping",)
    form_class = forms.PumpingForm
    success_url = reverse_lazy("core:pumping-list")
    success_message = _("%(model)s entry added!")

    def form_valid(self, form):
        combine_mode = form.cleaned_data.get("combine_mode") or "discrete"
        combine_target = form.cleaned_data.get("combine_target")
        # Pull the mode off the instance payload before save: Pumping.save
        # auto-creates the inventory unit; the merge must run after that
        # discrete unit exists (audit FK intact).
        if combine_mode == "into" and combine_target is not None:
            response = super().form_valid(form)
            source = models.FeedInventory.objects.filter(
                pumping_session=self.object
            ).order_by("-pk").first()
            if source is not None and source.pk != combine_target.pk:
                try:
                    combine_target.combine_into(
                        [source], keep_pumping_link=True
                    )
                    messages.success(
                        self.request,
                        _("Merged %(src)s into %(tgt)s.")
                        % {"src": source.label, "tgt": combine_target.label},
                    )
                except ValueError as err:
                    messages.warning(self.request, str(err))
            return response
        return super().form_valid(form)


class PumpingUpdate(CoreUpdateView):
    model = models.Pumping
    permission_required = ("core.change_pumping",)
    form_class = forms.PumpingForm
    success_url = reverse_lazy("core:pumping-list")
    success_message = _("%(model)s entry for %(child)s updated.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # BUG-1: expose Milk Inventory entries auto-created from this
        # pumping session so the form page can show the link (FR-5).
        context["inventory_items"] = models.FeedInventory.objects.filter(
            pumping_session=self.object
        )
        return context

    def form_valid(self, form):
        """Sync-if-pristine on amount edits (2026-08-17 decision B).

        A pristine auto-created unit follows the log's amount; a unit
        with any transaction history stays untouched and the user is
        warned about the divergence instead.
        """
        response = super().form_valid(form)
        if form.instance.pk:
            synced, reason = form.instance.sync_unit_amount_if_pristine()
            if not synced and reason in ("has_history", "touched_amount",
                                         "multi_unit"):
                unit = (
                    form.instance.source_inventory.order_by("-amount")
                    .first()
                )
                if unit:
                    messages.warning(
                        self.request,
                        _("Milk Inventory unit {} ({} ml) was NOT adjusted — "
                          "it has transaction history. Edit it directly if "
                          "needed.").format(
                              unit.label, unit.amount_remaining or 0
                          ),
                    )
        return response


class PumpingDelete(CoreDeleteView):
    model = models.Pumping
    permission_required = ("core.delete_pumping",)
    success_url = reverse_lazy("core:pumping-list")


class SleepList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Sleep
    template_name = "core/sleep_list.html"
    permission_required = ("core.view_sleep",)
    filterset_class = filters.SleepFilter


class SleepAdd(CoreAddView):
    model = models.Sleep
    permission_required = ("core.add_sleep",)
    form_class = forms.SleepForm
    success_url = reverse_lazy("core:sleep-list")


class SleepUpdate(CoreUpdateView):
    model = models.Sleep
    permission_required = ("core.change_sleep",)
    form_class = forms.SleepForm
    success_url = reverse_lazy("core:sleep-list")


class SleepDelete(CoreDeleteView):
    model = models.Sleep
    permission_required = ("core.delete_sleep",)
    success_url = reverse_lazy("core:sleep-list")


class TagAdminList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.Tag
    template_name = "core/tag_list.html"
    permission_required = ("core.view_tags",)
    filterset_class = filters.TagFilter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(Count("core_tagged_items"))
            .order_by(Lower("name"))
        )


class TagAdminDetail(PermissionRequiredMixin, DetailView):
    model = models.Tag
    permission_required = ("core.view_tags",)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            Count("feeding"),
            Count("diaperchange"),
            Count("pumping"),
            Count("sleep"),
            Count("tummytime"),
            Count("bmi"),
            Count("headcircumference"),
            Count("height"),
            Count("temperature"),
            Count("weight"),
        )
        return qs


class TagAdminAdd(CoreAddView):
    model = models.Tag
    permission_required = ("core.add_tag",)
    form_class = forms.TagAdminForm
    success_url = reverse_lazy("core:tag-list")


class TagAdminUpdate(CoreUpdateView):
    model = models.Tag
    permission_required = ("core.change_tag",)
    form_class = forms.TagAdminForm
    success_url = reverse_lazy("core:tag-list")


class TagAdminDelete(CoreDeleteView):
    model = models.Tag
    permission_required = ("core.delete_tag",)
    success_url = reverse_lazy("core:tag-list")

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(Count("core_tagged_items"))


class TemperatureList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.Temperature
    template_name = "core/temperature_list.html"
    permission_required = ("core.view_temperature",)
    filterset_class = filters.TemperatureFilter


class TemperatureAdd(CoreAddView):
    model = models.Temperature
    permission_required = ("core.add_temperature",)
    form_class = forms.TemperatureForm
    success_url = reverse_lazy("core:temperature-list")
    success_message = _("%(model)s reading added!")


class TemperatureUpdate(CoreUpdateView):
    model = models.Temperature
    permission_required = ("core.change_temperature",)
    form_class = forms.TemperatureForm
    success_url = reverse_lazy("core:temperature-list")
    success_message = _("%(model)s reading for %(child)s updated.")


class TemperatureDelete(CoreDeleteView):
    model = models.Temperature
    permission_required = ("core.delete_temperature",)
    success_url = reverse_lazy("core:temperature-list")


class DoctorVisitList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.DoctorVisit
    template_name = "core/doctorvisit_list.html"
    permission_required = ("core.view_doctorvisit",)
    paginate_by = 30


class DoctorVisitAdd(CoreAddView):
    model = models.DoctorVisit
    permission_required = ("core.add_doctorvisit",)
    form_class = forms.DoctorVisitForm
    success_url = reverse_lazy("core:doctorvisit-list")


class DoctorVisitUpdate(CoreUpdateView):
    model = models.DoctorVisit
    permission_required = ("core.change_doctorvisit",)
    form_class = forms.DoctorVisitForm
    success_url = reverse_lazy("core:doctorvisit-list")


class DoctorVisitDelete(CoreDeleteView):
    model = models.DoctorVisit
    permission_required = ("core.delete_doctorvisit",)
    success_url = reverse_lazy("core:doctorvisit-list")


class PrescriptionList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.Prescription
    template_name = "core/prescription_list.html"
    permission_required = ("core.view_prescription",)
    filterset_fields = ("child", "active", "medication_name")


class PrescriptionAdd(CoreAddView):
    model = models.Prescription
    permission_required = ("core.add_prescription",)
    form_class = forms.PrescriptionForm
    success_url = reverse_lazy("core:prescription-list")

    def get_initial(self):
        initial = super().get_initial()
        visit_id = self.request.GET.get("visit")
        if visit_id:
            try:
                visit = models.DoctorVisit.objects.get(pk=visit_id)
                initial["doctor_visit"] = visit
                initial["child"] = visit.child
                if visit.doctor_name:
                    initial["prescribing_doctor"] = visit.doctor_name
            except models.DoctorVisit.DoesNotExist:
                pass
        return initial


class PrescriptionUpdate(CoreUpdateView):
    model = models.Prescription
    permission_required = ("core.change_prescription",)
    form_class = forms.PrescriptionForm
    success_url = reverse_lazy("core:prescription-list")


class PrescriptionDelete(CoreDeleteView):
    model = models.Prescription
    permission_required = ("core.delete_prescription",)
    success_url = reverse_lazy("core:prescription-list")


class Timeline(LoginRequiredMixin, TemplateView):
    template_name = "timeline/timeline.html"

    # Show the overall timeline or a child timeline if one Child instance.
    def get(self, request, *args, **kwargs):
        children = models.Child.objects.count()
        if children == 1:
            return HttpResponseRedirect(
                reverse("core:child", args={models.Child.objects.first().slug})
            )
        return super(Timeline, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Timeline, self).get_context_data(**kwargs)
        date = self.request.GET.get("date", str(timezone.localdate()))
        _prepare_timeline_context_data(context, date)
        return context


class TimerList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Timer
    template_name = "core/timer_list.html"
    permission_required = ("core.view_timer",)
    filterset_fields = ("user",)


class TimerDetail(PermissionRequiredMixin, DetailView):
    model = models.Timer
    permission_required = ("core.view_timer",)


class TimerAdd(PermissionRequiredMixin, CreateView):
    model = models.Timer
    permission_required = ("core.add_timer",)
    form_class = forms.TimerForm

    def get_form_kwargs(self):
        kwargs = super(TimerAdd, self).get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

    def get_success_url(self):
        return reverse("core:timer-detail", kwargs={"pk": self.object.pk})


class TimerUpdate(CoreUpdateView):
    model = models.Timer
    permission_required = ("core.change_timer",)
    form_class = forms.TimerForm
    success_url = reverse_lazy("core:timer-list")

    def get_form_kwargs(self):
        kwargs = super(TimerUpdate, self).get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

    def get_success_url(self):
        instance = self.get_object()
        return reverse("core:timer-detail", kwargs={"pk": instance.pk})


class TimerAddQuick(PermissionRequiredMixin, RedirectView):
    http_method_names = ["post"]
    permission_required = ("core.add_timer",)

    def post(self, request, *args, **kwargs):
        instance = models.Timer.objects.create(user=request.user)
        # Find child from child pk in POST
        child_id = request.POST.get("child", False)
        child = models.Child.objects.get(pk=child_id) if child_id else None
        if child:
            instance.child = child
        # Add child relationship if there is only Child instance.
        # objects.count() not cached Child.count() — same staleness bug as
        # set_initial_values (bulk deletes bypass cache invalidation).
        elif models.Child.objects.count() == 1:
            instance.child = models.Child.objects.first()
        instance.save()
        self.url = request.GET.get(
            "next", reverse("core:timer-detail", args={instance.id})
        )
        return super(TimerAddQuick, self).get(request, *args, **kwargs)


class TimerRestart(PermissionRequiredMixin, RedirectView):
    http_method_names = ["post"]
    permission_required = ("core.change_timer",)

    def post(self, request, *args, **kwargs):
        instance = models.Timer.objects.get(id=kwargs["pk"])
        instance.restart()
        messages.success(request, "{} restarted.".format(instance))
        return super(TimerRestart, self).get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse("core:timer-detail", kwargs={"pk": kwargs["pk"]})


class TimerDelete(CoreDeleteView):
    model = models.Timer
    permission_required = ("core.delete_timer",)
    success_url = reverse_lazy("core:timer-list")


class TummyTimeList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.TummyTime
    template_name = "core/tummytime_list.html"
    permission_required = ("core.view_tummytime",)
    filterset_class = filters.TummyTimeFilter


class TummyTimeAdd(CoreAddView):
    model = models.TummyTime
    permission_required = ("core.add_tummytime",)
    form_class = forms.TummyTimeForm
    success_url = reverse_lazy("core:tummytime-list")


class TummyTimeUpdate(CoreUpdateView):
    model = models.TummyTime
    permission_required = ("core.change_tummytime",)
    form_class = forms.TummyTimeForm
    success_url = reverse_lazy("core:tummytime-list")


class TummyTimeDelete(CoreDeleteView):
    model = models.TummyTime
    permission_required = ("core.delete_tummytime",)
    success_url = reverse_lazy("core:tummytime-list")


class WeightList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Weight
    template_name = "core/weight_list.html"
    permission_required = ("core.view_weight",)
    filterset_class = filters.WeightFilter


class WeightAdd(CoreAddView):
    model = models.Weight
    permission_required = ("core.add_weight",)
    form_class = forms.WeightForm
    success_url = reverse_lazy("core:weight-list")


class WeightUpdate(CoreUpdateView):
    model = models.Weight
    permission_required = ("core.change_weight",)
    form_class = forms.WeightForm
    success_url = reverse_lazy("core:weight-list")


class WeightDelete(CoreDeleteView):
    model = models.Weight
    permission_required = ("core.delete_weight",)
    success_url = reverse_lazy("core:weight-list")


class SupplyItemRecalculate(PermissionRequiredMixin, RedirectView):
    permission_required = ("core.change_supplyitem",)

    def get(self, request, *args, **kwargs):
        from core.management.commands.recalculate_inventory import recalculate_inventory

        results = recalculate_inventory()
        for r in results:
            anchor_tag = " (anchored)" if r.get("anchored") else ""
            messages.info(
                request,
                f"{r['product']} [{r['size']}]: {r['before']} → {r['after']} "
                f"(baseline {r['baseline']}, consumed {r['consumed']}){anchor_tag}",
            )
        messages.success(
            request, f"Recalculated {len(results)} pool(s) from diaper change logs."
        )
        return HttpResponseRedirect(reverse("core:supplyitem-list"))


class SupplyItemRetire(PermissionRequiredMixin, View):
    """Wave 4 (2026-08-21): retire / un-retire a supply pool.

    Retired pools are hidden from add/restock pickers and never
    decremented, but stay visible on the Supplies page for history.
    """

    permission_required = ("core.change_supplyitem",)

    def post(self, request, pk):
        item = get_object_or_404(models.SupplyItem, pk=pk)
        retire = request.POST.get("mode", "retire") == "retire"
        item.is_retired = retire
        item.save(update_fields=["is_retired"])
        if retire:
            messages.success(request, f"Retired {item}.")
        else:
            messages.success(request, f"Restored {item} to active stock.")
        return HttpResponseRedirect(reverse("core:supplyitem-list"))


class SupplyItemList(PermissionRequiredMixin, ListView):
    model = models.SupplyItem
    template_name = "core/supplyitem_list.html"
    permission_required = ("core.view_supplyitem",)
    paginate_by = 50
    # Wave 4 (2026-08-21): subclasses (wipes page) can restrict to one
    # product-line item type.
    item_type_filter = None

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("product_line")
            .order_by(
                "product_line__item_type",
                "product_line__brand",
                "product_line__line",
                "size",
            )
        )
        if self.item_type_filter:
            qs = qs.filter(product_line__item_type=self.item_type_filter)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from collections import OrderedDict
        from django.utils import timezone

        child = context.get("unique_child") or models.Child.objects.first()
        if not child:
            return context

        items = models.SupplyItem.objects.filter(
            Q(child=child) | Q(child=None)
        ).select_related("product_line")
        if self.item_type_filter:
            items = items.filter(product_line__item_type=self.item_type_filter)
        # Group: type → brand → line → [items]
        grouped = OrderedDict()
        for item in items:
            pl = item.product_line
            type_label = pl.get_item_type_display()
            brand = pl.brand
            line = pl.line or ""

            if type_label not in grouped:
                grouped[type_label] = OrderedDict()
            if brand not in grouped[type_label]:
                grouped[type_label][brand] = OrderedDict()
            if line not in grouped[type_label][brand]:
                grouped[type_label][brand][line] = []
            grouped[type_label][brand][line].append(item)

        context["grouped_supplies"] = grouped

        # Diaper burn rate per size with selectable usage period:
        # fixed windows, all-time, or a custom from/to date range.
        # Math lives in core.inventory so /supplies and the dashboard
        # stock card always show identical numbers.
        from django.utils.dateparse import parse_date
        from datetime import datetime as _dt, time as _dtime, timedelta
        from core.inventory import compute_diaper_burn_table

        raw_days = self.request.GET.get("burn_days", "7")
        burn_from_raw = self.request.GET.get("burn_from", "").strip()
        burn_to_raw = self.request.GET.get("burn_to", "").strip()
        d_from = parse_date(burn_from_raw) if burn_from_raw else None
        d_to = parse_date(burn_to_raw) if burn_to_raw else None
        burn_all_time = raw_days == "all"
        burn_custom = not burn_all_time and (d_from or d_to)
        try:
            period_days = int(raw_days)
        except (TypeError, ValueError):
            period_days = 7
        if not burn_all_time and not burn_custom and period_days not in (7, 14, 30, 60):
            period_days = 7
        context["burn_days"] = "all" if burn_all_time else period_days
        context["burn_all_time"] = burn_all_time
        context["burn_custom"] = burn_custom
        context["burn_from"] = burn_from_raw
        context["burn_to"] = burn_to_raw
        context["burn_period_options"] = [7, 14, 30, 60]

        from_dt = to_dt = None
        if burn_custom:
            if d_from:
                from_dt = timezone.make_aware(_dt.combine(d_from, _dtime.min))
            if d_to:
                to_dt = timezone.make_aware(
                    _dt.combine(d_to, _dtime.min) + timedelta(days=1)
                )

        table = compute_diaper_burn_table(
            child,
            period_days=period_days,
            all_time=burn_all_time,
            from_dt=from_dt,
            to_dt=to_dt,
        )
        burn_rate = table["rows"]
        context["span_days"] = table["span_days"]
        context["stock_threshold"] = table["threshold_days"]
        if burn_rate:
            context["diaper_burn_rate"] = burn_rate

        return context



class WipesListView(SupplyItemList):
    """Wave 4 (2026-08-21): supplies page restricted to wipes lines."""

    item_type_filter = "wipes"
    template_name = "core/wipes_list.html"


class SupplyItemAdd(CoreAddView):
    model = models.SupplyItem
    permission_required = ("core.add_supplyitem",)
    form_class = forms.SupplyItemForm
    success_url = reverse_lazy("core:supplyitem-list")
    success_message = _("Supply item added!")


class SupplyItemUpdate(CoreUpdateView):
    model = models.SupplyItem
    permission_required = ("core.change_supplyitem",)
    form_class = forms.SupplyItemUpdateForm
    success_url = reverse_lazy("core:supplyitem-list")
    success_message = _("Supply item updated.")


class SupplyItemDelete(CoreDeleteView):
    model = models.SupplyItem
    permission_required = ("core.delete_supplyitem",)
    success_url = reverse_lazy("core:supplyitem-list")


class ProductLineList(PermissionRequiredMixin, ListView):
    model = models.ProductLine
    template_name = "core/productline_list.html"
    permission_required = ("core.view_productline",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from collections import OrderedDict

        grouped = OrderedDict()
        type_labels = dict(models.ProductLine.ITEM_TYPES)
        for pl in models.ProductLine.objects.all().order_by(
            "item_type", "brand", "line"
        ):
            label = type_labels.get(pl.item_type, pl.item_type)
            if label not in grouped:
                grouped[label] = []
            grouped[label].append(pl)
        context["grouped_products"] = grouped
        return context


class ProductLineAdd(CoreAddView):
    model = models.ProductLine
    permission_required = ("core.add_productline",)
    form_class = forms.ProductLineForm
    success_url = reverse_lazy("core:productline-list")
    success_message = _("Product line added!")


class ProductLineUpdate(CoreUpdateView):
    model = models.ProductLine
    permission_required = ("core.change_productline",)
    form_class = forms.ProductLineForm
    success_url = reverse_lazy("core:productline-list")


class ProductLineDelete(CoreDeleteView):
    model = models.ProductLine
    permission_required = ("core.delete_productline",)
    success_url = reverse_lazy("core:productline-list")


class SpitUpList(PermissionRequiredMixin, ListView):
    model = models.SpitUp
    template_name = "core/spitup_list.html"
    permission_required = ("core.view_spitup",)
    paginate_by = 30


class SpitUpAdd(CoreAddView):
    model = models.SpitUp
    permission_required = ("core.add_spitup",)
    form_class = forms.SpitUpForm
    success_url = reverse_lazy("core:spitup-list")
    success_message = _("Spit-up entry added!")


class SpitUpUpdate(CoreUpdateView):
    model = models.SpitUp
    permission_required = ("core.change_spitup",)
    form_class = forms.SpitUpForm
    success_url = reverse_lazy("core:spitup-list")
    success_message = _("Spit-up entry updated.")


class SpitUpDelete(CoreDeleteView):
    model = models.SpitUp
    permission_required = ("core.delete_spitup",)
    success_url = reverse_lazy("core:spitup-list")


class ActivityReport(LoginRequiredMixin, TemplateView):
    """
    Printable activity report for pediatrician/LC visits.
    Configurable date range, shows key stats from all BabyBuddy models.
    """

    template_name = "core/activity_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import timedelta, datetime as dt
        from django.db.models import Sum, Count, Avg, Q

        child = context.get("unique_child") or models.Child.objects.first()
        if not child:
            return context

        # Parse date range from query params, default to last 7 days
        today = timezone.localtime().date()
        end_date = self.request.GET.get("end_date", today.strftime("%Y-%m-%d"))
        days_back = int(self.request.GET.get("days", 7))
        start_date = self.request.GET.get("start_date")

        if start_date:
            try:
                start_dt = dt.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                start_dt = today - timedelta(days=days_back)
        else:
            start_dt = today - timedelta(days=days_back)

        try:
            end_dt = dt.strptime(end_date, "%Y-%m-%d")
        except (ValueError, NameError):
            end_dt = today

        # Convert to datetime range for queries
        dt_start = (
            timezone.make_aware(dt.combine(start_dt, dt.min.time()))
            if not isinstance(start_dt, type(timezone.now()))
            else start_dt
        )
        dt_end = (
            timezone.make_aware(dt.combine(end_dt, dt.max.time()))
            if not isinstance(end_dt, type(timezone.now()))
            else end_dt
        )

        context["child"] = child
        context["start_date"] = (
            start_dt.strftime("%Y-%m-%d") if hasattr(start_dt, "strftime") else start_dt
        )
        context["end_date"] = (
            end_dt.strftime("%Y-%m-%d") if hasattr(end_dt, "strftime") else end_dt
        )
        context["days"] = days_back

        # --- Feedings ---
        feedings = models.Feeding.objects.filter(
            child=child, end__range=[dt_start, dt_end]
        )
        feeding_total = 0
        feeding_count = feedings.count()
        for f in feedings:
            val = (
                f.amount_normalized
                if f.amount_normalized is not None
                else (f.amount or 0)
            )
            feeding_total += val

        # Feeding method breakdown
        from collections import Counter

        method_counts = Counter(f.get_method_display() for f in feedings)

        # Avg per day
        actual_days = (
            max((end_dt.date() - start_dt).days, 1)
            if hasattr(end_dt, "date")
            else max((end_dt - start_dt).days, 1)
        )
        avg_feedings_day = round(feeding_count / actual_days, 1)
        avg_ml_day = round(feeding_total / actual_days)

        feeding_total_ml = round(feeding_total)
        context["feeding_summary"] = {
            "count": feeding_count,
            "total_ml": feeding_total_ml,
            "total_oz": round(feeding_total_ml / 29.5735, 1),
            "avg_per_day": avg_feedings_day,
            "avg_ml_per_day": avg_ml_day,
            "avg_oz_per_day": round(avg_ml_day / 29.5735, 1),
            "methods": dict(method_counts.most_common()),
        }

        # --- Diaper Changes ---
        # Note: wet and solid are independent booleans (a change can be both).
        # We track them separately and note the overlap for accurate reporting.
        changes = models.DiaperChange.objects.filter(
            child=child, time__range=[dt_start, dt_end]
        )
        total_changes = changes.count()
        wet_count = changes.filter(wet=True).count()
        solid_count = changes.filter(solid=True).count()
        both_count = changes.filter(wet=True, solid=True).count()
        blowout_count = (
            changes.filter(blowout=True).count()
            if hasattr(changes.first(), "blowout")
            else 0
        )

        context["diaper_summary"] = {
            "total": total_changes,
            "wet": wet_count,
            "solid": solid_count,
            "both": both_count,
            "blowouts": blowout_count,
            "avg_per_day": round(total_changes / actual_days, 1),
            "avg_wet_per_day": round(wet_count / actual_days, 1),
            "avg_solid_per_day": round(solid_count / actual_days, 1),
        }

        # --- Sleep ---
        sleep_sessions = models.Sleep.objects.filter(
            child=child, end__range=[dt_start, dt_end]
        )
        sleep_total_minutes = 0
        for s in sleep_sessions:
            if s.duration:
                sleep_total_minutes += s.duration.total_seconds() / 60
        nap_count = 0
        if hasattr(sleep_sessions.first(), "nap"):
            nap_count = sleep_sessions.filter(nap=True).count()

        context["sleep_summary"] = {
            "sessions": sleep_sessions.count(),
            "total_hours": round(sleep_total_minutes / 60, 1),
            "avg_hours_day": round(sleep_total_minutes / 60 / actual_days, 1),
            "naps": nap_count,
        }

        # --- Pumping ---
        pumping_sessions = models.Pumping.objects.filter(
            child=child, end__range=[dt_start, dt_end]
        )
        pumping_total = 0
        for p in pumping_sessions:
            val = (
                p.amount_normalized
                if p.amount_normalized is not None
                else (p.amount or 0)
            )
            pumping_total += val

        pumping_count = pumping_sessions.count()
        pumping_total_ml = round(pumping_total)
        avg_ml_per_session = (
            round(pumping_total / pumping_count) if pumping_count > 0 else 0
        )
        context["pumping_summary"] = {
            "count": pumping_count,
            "total_ml": pumping_total_ml,
            "total_oz": round(pumping_total_ml / 29.5735, 1),
            "avg_per_day": round(pumping_count / actual_days, 1),
            "avg_ml_per_session": avg_ml_per_session,
            "avg_oz_per_session": (
                round(avg_ml_per_session / 29.5735, 1) if pumping_count > 0 else 0
            ),
        }

        # --- Weight ---
        weights = models.Weight.objects.filter(
            child=child, date__range=[start_dt, end_dt]
        ).order_by("date")
        weight_list = [{"date": w.date, "weight": w.weight} for w in weights]
        weight_change = None
        if len(weight_list) >= 2:
            weight_change = round(
                weight_list[-1]["weight"] - weight_list[0]["weight"], 3
            )

        context["weight_summary"] = {
            "entries": weight_list,
            "latest": weight_list[-1]["weight"] if weight_list else None,
            "earliest": weight_list[0]["weight"] if weight_list else None,
            "change": weight_change,
        }

        # --- Medications ---
        meds = (
            models.Medication.objects.filter(
                child=child, time__range=[dt_start, dt_end]
            )
            if hasattr(models, "Medication")
            else []
        )
        context["medication_summary"] = {
            "count": len(list(meds)),
        }

        # --- Spit-ups ---
        spitups = (
            models.SpitUp.objects.filter(child=child, time__range=[dt_start, dt_end])
            if hasattr(models, "SpitUp")
            else []
        )
        spitup_list = list(spitups)
        spitup_count = len(spitup_list)
        amount_counts = Counter(s.get_amount_display() for s in spitup_list if s.amount)
        by_amount_percentages = (
            {
                amount: round(count / spitup_count * 100, 1)
                for amount, count in amount_counts.items()
            }
            if spitup_count > 0
            else {}
        )
        context["spitup_summary"] = {
            "count": spitup_count,
            "by_amount": dict(amount_counts),
            "by_amount_percentages": by_amount_percentages,
            "by_amount_breakdown": [
                {
                    "amount": amount,
                    "count": count,
                    "percent": by_amount_percentages[amount],
                }
                for amount, count in amount_counts.items()
            ],
            "avg_per_day": round(spitup_count / actual_days, 1),
            "first_episode": min(s.time for s in spitup_list) if spitup_list else None,
            "last_episode": max(s.time for s in spitup_list) if spitup_list else None,
        }

        # --- Tummy Time ---
        tummy = models.TummyTime.objects.filter(
            child=child, end__range=[dt_start, dt_end]
        )
        tummy_total = 0
        for t in tummy:
            if t.duration:
                tummy_total += t.duration.total_seconds() / 60

        context["tummytime_summary"] = {
            "count": tummy.count(),
            "total_minutes": round(tummy_total),
            "avg_minutes_day": round(tummy_total / actual_days),
        }

        # Recent entries for the detail section
        context["recent_feedings"] = feedings.order_by("-end")[:10]
        context["recent_changes"] = changes.order_by("-time")[:10]

        # --- Trend comparison vs previous period ---
        prev_end = dt_start
        prev_start = prev_end - timedelta(days=actual_days)
        prev_dt_start = timezone.make_aware(dt.combine(prev_start, dt.min.time()))
        prev_dt_end = timezone.make_aware(dt.combine(prev_end, dt.max.time()))

        def _trend(current, previous):
            """Return (direction, pct_change) for two values."""
            if previous == 0:
                return ("→", None) if current == 0 else ("↑", None)
            pct = round((current - previous) / previous * 100)
            if abs(pct) < 5:
                return ("→", pct)
            return ("↑" if pct > 0 else "↓", abs(pct))

        # Previous period feeding volume
        prev_feedings = models.Feeding.objects.filter(
            child=child, end__range=[prev_dt_start, prev_dt_end]
        )
        prev_feeding_total = 0
        for f in prev_feedings:
            val = (
                f.amount_normalized
                if f.amount_normalized is not None
                else (f.amount or 0)
            )
            prev_feeding_total += val

        context["feeding_summary"]["trend_count"] = _trend(
            feeding_count, prev_feedings.count()
        )
        context["feeding_summary"]["trend_volume"] = _trend(
            context["feeding_summary"]["total_ml"], round(prev_feeding_total)
        )
        context["feeding_summary"]["prev_count"] = prev_feedings.count()
        context["feeding_summary"]["prev_volume"] = round(prev_feeding_total)

        # Previous period diaper changes
        prev_changes = models.DiaperChange.objects.filter(
            child=child, time__range=[prev_dt_start, prev_dt_end]
        )
        context["diaper_summary"]["trend_total"] = _trend(
            total_changes, prev_changes.count()
        )
        context["diaper_summary"]["prev_total"] = prev_changes.count()

        # Previous period pumping
        prev_pumping = models.Pumping.objects.filter(
            child=child, end__range=[prev_dt_start, prev_dt_end]
        )
        prev_pumping_total = 0
        for p in prev_pumping:
            val = (
                p.amount_normalized
                if p.amount_normalized is not None
                else (p.amount or 0)
            )
            prev_pumping_total += val

        context["pumping_summary"]["trend_count"] = _trend(
            pumping_sessions.count(), prev_pumping.count()
        )
        context["pumping_summary"]["trend_volume"] = _trend(
            context["pumping_summary"]["total_ml"], round(prev_pumping_total)
        )
        context["pumping_summary"]["prev_count"] = prev_pumping.count()
        context["pumping_summary"]["prev_volume"] = round(prev_pumping_total)

        # Previous period sleep
        prev_sleep = models.Sleep.objects.filter(
            child=child, end__range=[prev_dt_start, prev_dt_end]
        )
        prev_sleep_minutes = 0
        for s in prev_sleep:
            if s.duration:
                prev_sleep_minutes += s.duration.total_seconds() / 60
        context["sleep_summary"]["trend_hours"] = _trend(
            context["sleep_summary"]["total_hours"],
            round(prev_sleep_minutes / 60, 1),
        )
        context["sleep_summary"]["prev_hours"] = round(prev_sleep_minutes / 60, 1)

        return context


class EquipmentItemList(PermissionRequiredMixin, ListView):
    model = models.EquipmentItem
    template_name = "core/equipmentitem_list.html"
    permission_required = ("core.view_equipmentitem",)
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related("product_line", "child")
        # Default: show owned only, unless ?show_all=1
        if self.request.GET.get("show_all") != "1":
            qs = qs.filter(disposal_status="owned")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = list(self.get_queryset())
        from collections import defaultdict

        grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for item in items:
            grouped[item.product_line.item_type][item.product_line.brand][
                item.product_line.line
            ].append(item)
        # Convert to plain dicts: Django template resolution of `x.items`
        # does dict-key lookup FIRST, and a defaultdict auto-vivifies the
        # missing 'items' key to an empty dict — silently rendering nothing.
        context["grouped_equipment"] = {
            item_type: {
                brand: dict(lines) for brand, lines in brands.items()
            }
            for item_type, brands in grouped.items()
        }
        context["show_all"] = self.request.GET.get("show_all") == "1"
        return context


class EquipmentItemAdd(CoreAddView):
    model = models.EquipmentItem
    permission_required = ("core.add_equipmentitem",)
    form_class = forms.EquipmentItemForm
    success_url = reverse_lazy("core:equipment-list")
    success_message = _("Equipment added!")


class EquipmentItemUpdate(CoreUpdateView):
    model = models.EquipmentItem
    permission_required = ("core.change_equipmentitem",)
    form_class = forms.EquipmentItemForm
    success_url = reverse_lazy("core:equipment-list")
    success_message = _("Equipment updated.")


class EquipmentItemDelete(CoreDeleteView):
    model = models.EquipmentItem
    permission_required = ("core.delete_equipmentitem",)
    success_url = reverse_lazy("core:equipment-list")


class FeedInventoryList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.FeedInventory
    template_name = "core/feedinventory_list.html"
    permission_required = ("core.view_feedinventory",)
    filterset_class = filters.FeedInventoryFilter
    # use_by_info() inspects linked feedings for the leftover window —
    # prefetch to keep the list page free of per-row queries.
    queryset = models.FeedInventory.objects.prefetch_related("feedings")


class FeedInventoryAdd(CoreAddView):
    model = models.FeedInventory
    permission_required = ("core.add_feedinventory",)
    form_class = forms.FeedInventoryForm
    success_url = reverse_lazy("core:feedinventory-list")
    success_message = _("%(model)s entry added!")


class FeedInventoryUpdate(CoreUpdateView):
    model = models.FeedInventory
    permission_required = ("core.change_feedinventory",)
    form_class = forms.FeedInventoryForm
    success_url = reverse_lazy("core:feedinventory-list")
    success_message = _("%(model)s entry for %(child)s updated.")

    def form_valid(self, form):
        obj = form.instance
        transition_ctx = None
        # Warmed-no-cold-return guard (2026-08-17): model clean() blocks
        # this, but the transition-rewind path below intentionally skips
        # full-clean semantics, so enforce it here explicitly too.
        if obj.pk and obj.warmed_at and obj.storage_location in (
            "fridge",
            "freezer",
            "deep_freeze",
        ):
            form.add_error(
                "storage_location",
                _("This unit has been warmed — it cannot return to cold "
                  "storage (CDC-conservative: use or discard within its "
                  "2-hour clock)."),
            )
            return self.form_invalid(form)
        # Refreeze guard (CDC, 2026-08-21): a unit that has thawed can
        # never go back into a freezer. thaw_started_at is the durable
        # signal (set on first freezer exit); status=="thawed" covers
        # units that thawed before the field existed.
        if obj.pk and obj.storage_location in ("freezer", "deep_freeze"):
            prior = (
                models.FeedInventory.objects.filter(pk=obj.pk)
                .values("storage_location", "status", "thaw_started_at")
                .first()
            )
            if prior and (
                prior["thaw_started_at"] is not None
                or prior["status"] == "thawed"
            ):
                form.add_error(
                    "storage_location",
                    _("Thawed milk cannot be refrozen (CDC: never "
                      "refreeze breast milk after it has thawed). Use "
                      "it within the thawed window or discard it."),
                )
                return self.form_invalid(form)
        if obj.pk:
            prior = (
                models.FeedInventory.objects.filter(pk=obj.pk)
                .values("storage_location", "status")
                .first()
            )
            if prior and (
                obj.storage_location != prior["storage_location"]
                or obj.status != prior["status"]
            ) and obj.status not in ("used", "discarded"):
                # _transition_mutate reads self.status/self.storage_location
                # as the OLD state — rewind to the persisted values first,
                # then mutate toward the submitted location.
                new_location = obj.storage_location
                obj.storage_location = prior["storage_location"]
                obj.status = prior["status"]
                old_location, old_status, events = obj._transition_mutate(
                    new_location, timezone.now()
                )
                transition_ctx = (old_location, old_status, events)
        response = super().form_valid(form)
        if transition_ctx:
            form.instance._write_transition_events(
                *transition_ctx, note="Location/status edit"
            )
        return response


class FeedInventoryDelete(CoreDeleteView):
    model = models.FeedInventory
    permission_required = ("core.delete_feedinventory",)
    success_url = reverse_lazy("core:feedinventory-list")


class FeedInventoryConsume(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    """Consume a partial amount from a FeedInventory entry."""

    template_name = "core/feedinventory_consume.html"
    permission_required = ("core.change_feedinventory",)
    form_class = forms.ConsumeFeedInventoryForm
    success_url = reverse_lazy("core:feedinventory-list")

    def get_object(self):
        return models.FeedInventory.objects.get(pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inventory"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        inventory = self.get_object()
        consume_amount = form.cleaned_data["amount"]
        inventory.amount_remaining = round(
            (inventory.amount_remaining or 0) - consume_amount, 2
        )
        if inventory.amount_remaining <= 0:
            inventory.amount_remaining = 0
            inventory.status = "used"
        inventory.save()
        inventory.record_event(
            "consume_manual",
            amount_delta=-consume_amount,
            note="Manual consume from inventory page",
        )
        self.success_message = _(
            "Consumed %(amount).1f ml from feed inventory entry (%(remaining).1f ml remaining)."
        ) % {"amount": consume_amount, "remaining": inventory.amount_remaining}
        return super().form_valid(form)


class FeedInventoryDiscard(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    """Discard remaining amount from a FeedInventory entry."""

    template_name = "core/feedinventory_discard.html"
    permission_required = ("core.change_feedinventory",)
    form_class = Form  # simple confirm form (no fields)
    success_url = reverse_lazy("core:feedinventory-list")

    def get_object(self):
        return models.FeedInventory.objects.get(pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        inventory = self.get_object()
        inventory.amount_remaining = 0
        inventory.status = "discarded"
        inventory.save()
        inventory.record_event(
            "discarded",
            amount_delta=0,
            note="Discarded from inventory page",
        )
        self.success_message = _("Feed inventory entry discarded.")
        return super().form_valid(form)
class FeedInventoryCombine(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    """Combine (merge) other fresh entries into this entry."""

    template_name = "core/feedinventory_combine.html"
    permission_required = ("core.change_feedinventory",)
    form_class = forms.CombineFeedInventoryForm
    success_url = reverse_lazy("core:feedinventory-list")

    def get_object(self):
        return models.FeedInventory.objects.get(pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inventory"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        inventory = self.get_object()
        entries = list(form.cleaned_data["entries"])
        survivor = form.cleaned_data.get("survivor") or inventory
        # Merge set = target + selected entries (+ the chosen survivor if
        # it wasn't among them). Everything but the survivor is absorbed.
        units = {u.pk: u for u in [inventory, survivor] + entries}
        if survivor.pk not in units:
            units[survivor.pk] = survivor
        to_merge = [u for pk, u in units.items() if pk != survivor.pk]
        merged, _absorbed = survivor.combine_into(to_merge)
        self.success_message = ngettext(
            "Combined %(n)d entry (%(ml).1f ml merged) into unit #%(spk)d.",
            "Combined %(n)d entries (%(ml).1f ml merged) into unit #%(spk)d.",
            len(to_merge),
        ) % {"n": len(to_merge), "ml": merged, "spk": survivor.pk}
        return super().form_valid(form)


class FeedInventoryCombineInto(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    """Reverse combine: merge this unit into a chosen target unit."""

    template_name = "core/feedinventory_combine_into.html"
    permission_required = ("core.change_feedinventory",)
    form_class = forms.CombineIntoFeedInventoryForm
    success_url = reverse_lazy("core:feedinventory-list")

    def get_object(self):
        return models.FeedInventory.objects.get(pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inventory"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        inventory = self.get_object()
        target = form.cleaned_data["target"]
        target.combine_into([inventory])
        self.success_message = _(
            "Merged %(src)s into %(tgt)s."
        ) % {"src": inventory.label, "tgt": target.label}
        return super().form_valid(form)


class FeedInventoryWarm(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    """B2 (2026-08-21): one-way Mark warmed action on a milk unit."""

    template_name = "core/feedinventory_warm.html"
    permission_required = ("core.change_feedinventory",)
    form_class = forms.MarkWarmedForm
    success_url = reverse_lazy("core:feedinventory-list")

    def get_object(self):
        return models.FeedInventory.objects.get(pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        inventory = self.get_object()
        try:
            inventory.mark_warmed(
                warmed_at=form.cleaned_data["warmed_at"],
                user=self.request.user if self.request.user.is_authenticated else None,
            )
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        if form.cleaned_data.get("note"):
            inventory.record_event(
                "warmed",
                note="User note: {}".format(form.cleaned_data["note"]),
            )
        self.success_message = _("Marked warmed - 2h clock started.")
        return super().form_valid(form)


class FeedInventorySplit(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    """Split off a portion of this entry into a new entry."""

    template_name = "core/feedinventory_split.html"
    permission_required = ("core.add_feedinventory", "core.change_feedinventory")
    form_class = forms.SplitFeedInventoryForm
    success_url = reverse_lazy("core:feedinventory-list")

    def get_object(self):
        return models.FeedInventory.objects.get(pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inventory"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        inventory = self.get_object()
        split_amount = form.cleaned_data["amount"]
        new_storage = form.cleaned_data["storage_location"]
        new_status = form.cleaned_data["status"]
        new_entry = models.FeedInventory(
            child=inventory.child,
            type=inventory.type,
            amount=split_amount,
            amount_unit="ml",
            amount_remaining=split_amount,
            storage_location=new_storage,
            status=new_status,
            expressed_at=inventory.expressed_at,
            notes=_("Split from entry #%(pk)d") % {"pk": inventory.pk},
        )
        # Inherit the storage-history clocks that exist in the source's
        # current state (the split-off portion shares the unit's history).
        if inventory.fridge_entered_at is not None:
            new_entry.fridge_entered_at = inventory.fridge_entered_at
        if inventory.freezer_entered_at is not None:
            new_entry.freezer_entered_at = inventory.freezer_entered_at
        if inventory.thaw_started_at is not None:
            new_entry.thaw_started_at = inventory.thaw_started_at
        if inventory.thaw_completed_at is not None:
            new_entry.thaw_completed_at = inventory.thaw_completed_at
        if inventory.warmed_at is not None:
            new_entry.warmed_at = inventory.warmed_at
        new_entry.save()
        # The split-off unit starts its own stint clock for its chosen
        # location (the source's stint fields stay with the source).
        if new_storage == "room_temp" and new_entry.room_temp_since is None:
            new_entry.room_temp_since = timezone.now()
            new_entry.save(update_fields=["room_temp_since"])
        elif new_storage == "cooler" and new_entry.cooler_entered_at is None:
            new_entry.cooler_entered_at = timezone.now()
            new_entry.save(update_fields=["cooler_entered_at"])
        new_entry.record_event(
            "split_to",
            amount_delta=0,
            counterpart=inventory,
            note="Split off from entry #{}".format(inventory.pk),
        )
        inventory.amount_remaining = round(
            (inventory.amount_remaining or 0) - split_amount, 2
        )
        inventory.save()
        inventory.record_event(
            "split_off",
            amount_delta=-split_amount,
            counterpart=new_entry,
            note="Split off {} ml into entry #{}".format(split_amount, new_entry.pk),
        )
        self.success_message = _(
            "Split %(amount).1f ml into a new entry (#%(newpk)d); %(rem).1f ml remains."
        ) % {"amount": split_amount, "newpk": new_entry.pk, "rem": inventory.amount_remaining}
        return super().form_valid(form)


class SupplyItemAdjust(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    """Manually adjust a pool's quantity with an audit trail."""
    template_name = "core/supplyitem_adjust.html"
    permission_required = ("core.change_supplyitem",)
    form_class = forms.SupplyItemAdjustForm
    success_url = reverse_lazy("core:supplyitem-list")

    def get_object(self):
        return models.SupplyItem.objects.get(pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["supply_item"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        item = self.get_object()
        physical_count = form.cleaned_data["physical_count"]
        count_time = form.cleaned_data["count_time"]
        reason = form.cleaned_data["reason"]

        system_before = item.quantity

        # Create the adjustment record
        adjustment = models.InventoryAdjustment.objects.create(
            supply_item=item,
            count_time=count_time,
            physical_count=physical_count,
            reason=reason,
            adjustment_type="manual_adjust",
            system_count_before=system_before,
        )

        # Update pool quantity immediately
        item.quantity = physical_count
        item.save(update_fields=["quantity"])

        # Create audit transaction
        models.InventoryTransaction.objects.create(
            supply_item=item,
            delta=physical_count - system_before,
            transaction_type="adjustment",
            source_id=adjustment.pk,
            quantity_after=item.quantity,
            note=reason,
        )

        messages.success(
            self.request,
            f"Adjusted {item}: {system_before} -> {physical_count}.",
        )
        return super().form_valid(form)


class InventoryTransactionList(PermissionRequiredMixin, ListView):
    """Show transaction history for a specific pool."""
    model = models.InventoryTransaction
    template_name = "core/inventorytransaction_list.html"
    permission_required = ("core.view_supplyitem",)
    paginate_by = 50

    def get_queryset(self):
        qs = models.InventoryTransaction.objects.select_related(
            "supply_item__product_line"
        )
        pool_id = self.request.GET.get("pool")
        if pool_id:
            qs = qs.filter(supply_item_id=pool_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pool_id = self.request.GET.get("pool")
        if pool_id:
            context["pool"] = models.SupplyItem.objects.filter(pk=pool_id).first()
        return context


class SupplyItemOpenPackage(PermissionRequiredMixin, RedirectView):
    """Quick action: set usage_eligible to now, making the pool eligible for decrement."""
    permission_required = ("core.change_supplyitem",)

    def get(self, request, *args, **kwargs):
        from django.utils import timezone
        item = models.SupplyItem.objects.get(pk=kwargs["pk"])
        item.usage_eligible = timezone.now()
        item.save(update_fields=["usage_eligible"])

        # Create audit transaction
        models.InventoryTransaction.objects.create(
            supply_item=item,
            delta=0,
            transaction_type="adjustment",
            quantity_after=item.quantity,
            note="Package opened — set usage_eligible",
        )

        messages.success(
            request,
            f"Opened {item}: now eligible for decrement.",
        )
        return HttpResponseRedirect(reverse("core:supplyitem-list"))


class PhysicalCountEntry(PermissionRequiredMixin, TemplateView):
    """Multi-line physical count entry with dry-run support."""
    template_name = "core/physical_count.html"
    permission_required = ("core.change_supplyitem",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.forms import formset_factory
        from core.forms import PhysicalCountForm, PhysicalCountLineForm
        LineFormSet = formset_factory(PhysicalCountLineForm, extra=5, can_delete=True)
        context["header_form"] = PhysicalCountForm()
        context["line_formset"] = LineFormSet()
        return context

    def post(self, request, *args, **kwargs):
        from django.forms import formset_factory
        from core.forms import PhysicalCountForm, PhysicalCountLineForm
        from core.models import SupplyItem, InventoryAdjustment, InventoryTransaction
        from django.utils import timezone
        from django.contrib import messages

        header_form = PhysicalCountForm(request.POST)
        LineFormSet = formset_factory(PhysicalCountLineForm, extra=5, can_delete=True)
        line_formset = LineFormSet(request.POST)

        if not header_form.is_valid() or not line_formset.is_valid():
            return self.render_to_response(
                self.get_context_data(
                    header_form=header_form,
                    line_formset=line_formset,
                )
            )

        count_time = header_form.cleaned_data["count_time"]
        dry_run = header_form.cleaned_data["dry_run"]
        notes = header_form.cleaned_data.get("notes", "")
        session_id = str(uuid.uuid4()) if not dry_run else ""

        # Collect valid lines
        lines = []
        counted_brands = set()  # track brands for mixed-count exclusion
        for form in line_formset:
            if form.cleaned_data.get("physical_count") is None:
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            product = form.cleaned_data.get("product", "")
            size = form.cleaned_data.get("size", "")
            count = form.cleaned_data["physical_count"]
            brand = ""
            line = ""
            if product and "||" in product:
                parts = product.split("||", 1)
                brand = parts[0]
                line = parts[1] if len(parts) > 1 else ""
            lines.append({
                "brand": brand,
                "line": line,
                "size": size,
                "count": count,
            })
            if brand:
                counted_brands.add((brand, line))

        if not lines:
            messages.error(request, _("No valid count lines entered."))
            return self.render_to_response(
                self.get_context_data(header_form=header_form, line_formset=line_formset)
            )

        # Process each line — distribute across matching pools FIFO
        results = []
        for line_data in lines:
            brand = line_data["brand"]
            line_name = line_data["line"]
            size = line_data["size"]
            total_count = line_data["count"]

            # Find matching pools
            pools_qs = SupplyItem.objects.select_related("product_line").filter(
                product_line__item_type="diapers",
                size=size,
            )

            # Filter in Python (SQLite None-guard)
            pools = []
            for p in pools_qs:
                if p.usage_eligible is None:
                    continue
                if p.is_reserve:
                    continue
                if brand:
                    if p.product_line.brand != brand:
                        continue
                    if (p.product_line.line or "") != line_name:
                        continue
                else:
                    # Size-only: exclude brands already counted on other lines
                    if (p.product_line.brand, p.product_line.line or "") in counted_brands:
                        continue
                pools.append(p)

            pools_sorted = sorted(pools, key=lambda p: (p.usage_eligible, p.id))

            # Distribute count across pools: FIFO consume from oldest-opened
            # pools; the LAST pool (most recently opened) absorbs any surplus
            # so the counted total always lands on-hand exactly once.
            remaining = total_count
            last_idx = len(pools_sorted) - 1
            for idx, pool in enumerate(pools_sorted):
                current = pool.quantity
                if idx == last_idx:
                    pool_count = max(remaining, 0)
                else:
                    pool_count = min(current, remaining)
                remaining -= pool_count

                if pool_count == current:
                    continue  # no change needed

                results.append({
                    "pool": pool,
                    "before": current,
                    "after": pool_count,
                    "brand": brand or "(all)",
                    "size": size,
                    "line_count": total_count,
                })

                if not dry_run:
                    adj = InventoryAdjustment.objects.create(
                        supply_item=pool,
                        count_time=count_time,
                        physical_count=pool_count,
                        reason=notes or "Physical count",
                        adjustment_type="snapshot_brand" if brand else "snapshot_size_only",
                        session_id=session_id,
                        system_count_before=current,
                    )
                    pool.quantity = pool_count
                    pool.save(update_fields=["quantity"])
                    InventoryTransaction.objects.create(
                        supply_item=pool,
                        delta=pool_count - current,
                        transaction_type="adjustment",
                        source_id=adj.pk,
                        quantity_after=pool.quantity,
                        note=notes or "Physical count",
                    )

        # Build summary message
        if dry_run:
            messages.info(request, _(
                f"DRY RUN — {len(results)} pool(s) would be adjusted. "
                f"Toggle off 'Preview only' and submit to apply."
            ))
        else:
            messages.success(request, _(
                f"Physical count applied — {len(results)} pool(s) adjusted."
            ))

        # Show results in context
        context = self.get_context_data()
        context["results"] = results
        context["dry_run"] = dry_run
        context["header_form"] = header_form
        context["line_formset"] = LineFormSet()
        return self.render_to_response(context)


import uuid


class FormulaStockList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    template_name = "core/formulastock_list.html"
    model = models.FormulaStock
    filterset_class = filters.FormulaStockFilter
    permission_required = "core.view_formulastock"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("product_line")
            .order_by(
                "is_reserve",
                "-drain_priority",
                "product_line__brand",
                "product_line__line",
                "opened_at",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        opened = qs.filter(opened_at__isnull=False)
        sealed = qs.filter(opened_at__isnull=True)
        context["formula_opened"] = opened
        context["formula_sealed"] = sealed
        return context


class FormulaStockOpen(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    """Open one sealed container from a pool (ledger-audited both sides)."""

    template_name = "core/formulastock_open.html"
    permission_required = ("core.change_formulastock",)
    form_class = forms.OpenFormulaStockForm
    success_url = reverse_lazy("core:formulastock-list")

    def get_object(self):
        return models.FormulaStock.objects.select_related(
            "product_line"
        ).get(pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        stock = self.get_object()
        try:
            opened_row = stock.open_container(
                opened_at=form.cleaned_data["opened_at"],
                user=self.request.user if self.request.user.is_authenticated else None,
            )
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        if form.cleaned_data.get("note"):
            opened_row.record_event(
                "opened",
                note="User note: {}".format(form.cleaned_data["note"]),
            )
        self.success_message = _(
            "Container opened - use-by clock started."
        )
        return super().form_valid(form)


class FormulaStockAdjust(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    """Manual adjust of an opened container's remaining amount."""

    template_name = "core/formulastock_adjust.html"
    permission_required = ("core.change_formulastock",)
    form_class = forms.FormulaStockAdjustForm
    success_url = reverse_lazy("core:formulastock-list")

    def get_object(self):
        return models.FormulaStock.objects.select_related(
            "product_line"
        ).get(pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["stock"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        return context

    def form_valid(self, form):
        from django.db import transaction

        stock = self.get_object()
        physical = form.cleaned_data["physical_amount"]
        reason = form.cleaned_data["reason"]
        note = form.cleaned_data.get("note", "")
        count_time = form.cleaned_data["count_time"]

        is_powder = stock.form == "powder"
        current = (
            stock.grams_remaining if is_powder else stock.ml_remaining
        ) or 0
        delta = round(physical - current, 2)

        with transaction.atomic():
            if is_powder:
                stock.grams_remaining = physical
                update_fields = ["grams_remaining"]
            else:
                stock.ml_remaining = physical
                update_fields = ["ml_remaining"]
            stock.save(update_fields=update_fields)
            stock.record_event(
                "manual_adjust",
                delta_grams=delta if is_powder else None,
                delta_ml=None if is_powder else delta,
                grams_after=stock.grams_remaining,
                ml_after=stock.ml_remaining,
                note="Adjust ({reason}): {note} [counted {when}]".format(
                    reason=reason,
                    note=note or "-",
                    when=count_time.strftime("%Y-%m-%d %H:%M"),
                ),
            )

        self.success_message = _(
            "Adjusted to %(amount).1f %(unit)s (%(delta)+.1f %(unit)s)."
        ) % {
            "amount": physical,
            "unit": "g" if is_powder else "ml",
            "delta": delta,
    }
        return super().form_valid(form)


class FormulaStockAdd(CoreAddView):
    model = models.FormulaStock
    permission_required = ("core.add_formulastock",)
    form_class = forms.FormulaStockForm
    success_url = reverse_lazy("core:formulastock-list")
    success_message = _("Formula stock added!")


class FormulaStockUpdate(CoreUpdateView):
    model = models.FormulaStock
    permission_required = ("core.change_formulastock",)
    form_class = forms.FormulaStockForm
    success_url = reverse_lazy("core:formulastock-list")


class FormulaStockDelete(CoreDeleteView):
    model = models.FormulaStock
    permission_required = ("core.delete_formulastock",)
    success_url = reverse_lazy("core:formulastock-list")


class PreparedFeedList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.PreparedFeed
    template_name = "core/preparedfeed_list.html"
    permission_required = ("core.view_preparedfeed",)
    filterset_class = filters.PreparedFeedFilter
    queryset = models.PreparedFeed.objects.select_related("source_pool", "source_pool__product_line")


class PreparedFeedAdd(CoreAddView):
    model = models.PreparedFeed
    permission_required = ("core.add_preparedfeed",)
    form_class = forms.PreparedFeedForm
    success_url = reverse_lazy("core:preparedfeed-list")
    success_message = _("Prepared feed logged!")


class PreparedFeedUpdate(CoreUpdateView):
    model = models.PreparedFeed
    permission_required = ("core.change_preparedfeed",)
    form_class = forms.PreparedFeedForm
    success_url = reverse_lazy("core:preparedfeed-list")


class PreparedFeedDelete(CoreDeleteView):
    model = models.PreparedFeed
    permission_required = ("core.delete_preparedfeed",)
    success_url = reverse_lazy("core:preparedfeed-list")
