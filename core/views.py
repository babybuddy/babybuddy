# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Exists, F, Max, Min, OuterRef, Prefetch, Q
from django.db.models.functions import Lower, TruncDate
from django.forms import Form
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView

from babybuddy.mixins import LoginRequiredMixin, PermissionRequiredMixin
from babybuddy.views import BabyBuddyFilterView, BabyBuddyPaginatedView
from core import filters, forms, models, timeline


def _prepare_timeline_context_data(context, date, child=None, user=None):
    date = timezone.datetime.strptime(date, "%Y-%m-%d")
    date = timezone.localtime(timezone.make_aware(date))
    context["timeline_objects"] = timeline.get_objects(
        date,
        child,
        include_meals=user is None or user.has_perm("core.view_meal"),
        can_edit_meals=user is None or user.has_perm("core.change_meal"),
    )
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
        for parameter in ["child", "timer"]:
            value = self.request.GET.get(parameter, None)
            if value:
                kwargs.update({parameter: value})
        return kwargs


class CoreUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    def get_success_message(self, cleaned_data):
        cleaned_data["model"] = self.model._meta.verbose_name.title()
        if "child" in cleaned_data:
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
        _prepare_timeline_context_data(context, date, self.object, self.request.user)
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


class FeedingUpdate(CoreUpdateView):
    model = models.Feeding
    permission_required = ("core.change_feeding",)
    form_class = forms.FeedingForm
    success_url = reverse_lazy("core:feeding-list")


class FeedingDelete(CoreDeleteView):
    model = models.Feeding
    permission_required = ("core.delete_feeding",)
    success_url = reverse_lazy("core:feeding-list")


class FoodList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Food
    template_name = "core/food_list.html"
    permission_required = ("core.view_food",)
    filterset_class = filters.FoodFilter


class FoodAdd(CoreAddView):
    model = models.Food
    permission_required = ("core.add_food",)
    form_class = forms.FoodForm
    success_url = reverse_lazy("core:food-list")


class FoodUpdate(CoreUpdateView):
    model = models.Food
    permission_required = ("core.change_food",)
    form_class = forms.FoodForm
    success_url = reverse_lazy("core:food-list")


class FoodQuickAdd(PermissionRequiredMixin, View):
    permission_required = ("core.add_food",)

    def post(self, request, *args, **kwargs):
        form = forms.FoodForm(request.POST)
        if not form.is_valid():
            return JsonResponse(
                {"errors": form.errors.get_json_data()},
                status=400,
            )
        food = form.save()
        return JsonResponse(
            {
                "id": food.pk,
                "name": food.name,
                "category": food.get_category_display(),
            },
            status=201,
        )


class MealList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Meal
    template_name = "core/meal_list.html"
    permission_required = ("core.view_meal",)
    filterset_class = filters.MealFilter

    @staticmethod
    def meal_foods_with_introduction_status():
        previous_consumption = models.MealFood.objects.filter(
            food_id=OuterRef("food_id"),
            meal__child_id=OuterRef("meal__child_id"),
        ).filter(
            Q(meal__time__lt=OuterRef("meal__time"))
            | Q(
                meal__time=OuterRef("meal__time"),
                meal_id__lt=OuterRef("meal_id"),
            )
        )
        return models.MealFood.objects.select_related("food").annotate(
            previously_consumed=Exists(previous_consumption)
        )

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                local_date=TruncDate(
                    "time",
                    tzinfo=timezone.get_current_timezone(),
                )
            )
            .select_related("child")
            .prefetch_related(
                Prefetch(
                    "mealfood_set",
                    queryset=self.meal_foods_with_introduction_status(),
                ),
                "tags",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible_meals = list(context["object_list"])
        visible_dates = {meal.local_date for meal in visible_meals}
        category_labels = dict(models.Food._meta.get_field("category").choices)

        for local_date in visible_dates:
            day_meals = self.object_list.filter(local_date=local_date)
            day_meal_foods = self.meal_foods_with_introduction_status().filter(
                meal__in=day_meals
            )
            foods = {}
            category_counts = {}
            new_foods = set()
            for meal_food in day_meal_foods:
                foods[meal_food.food_id] = meal_food.food.name
                category = meal_food.food.category
                category_counts[category] = category_counts.get(category, 0) + 1
                if meal_food.is_first_introduction:
                    new_foods.add(meal_food.food.name)
            summary = {
                "meal_count": day_meals.count(),
                "food_count": len(foods),
                "category_counts": [
                    (category_labels[category], count)
                    for category, count in sorted(category_counts.items())
                ],
                "new_foods": sorted(new_foods),
            }
            for meal in visible_meals:
                if meal.local_date == local_date:
                    meal.day_summary = summary
        return context


class MealAdd(CoreAddView):
    model = models.Meal
    permission_required = ("core.add_meal",)
    form_class = forms.MealForm
    success_url = reverse_lazy("core:meal-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MealUpdate(CoreUpdateView):
    model = models.Meal
    permission_required = ("core.change_meal",)
    form_class = forms.MealForm
    success_url = reverse_lazy("core:meal-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MealDelete(CoreDeleteView):
    model = models.Meal
    permission_required = ("core.delete_meal",)
    success_url = reverse_lazy("core:meal-list")


class ChildFoodProfileList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.ChildFoodProfile
    template_name = "core/child_food_profile_list.html"
    permission_required = ("core.view_childfoodprofile",)
    filterset_class = filters.ChildFoodProfileFilter

    def get_queryset(self):
        matching_child = Q(food__meals__child=F("child"))
        return (
            super()
            .get_queryset()
            .select_related("child", "food")
            .annotate(
                first_consumed=Min(
                    "food__meals__time",
                    filter=matching_child,
                ),
                last_consumed=Max(
                    "food__meals__time",
                    filter=matching_child,
                ),
                consumption_count=Count(
                    "food__meals",
                    filter=matching_child,
                    distinct=True,
                ),
            )
            .order_by("child__first_name", "food__name", "pk")
        )


class ChildFoodProfileAdd(CoreAddView):
    model = models.ChildFoodProfile
    template_name = "core/child_food_profile_form.html"
    permission_required = ("core.add_childfoodprofile",)
    form_class = forms.ChildFoodProfileForm
    success_url = reverse_lazy("core:child-food-profile-list")

    def get_initial(self):
        initial = super().get_initial()
        food_id = self.request.GET.get("food")
        if food_id:
            initial["food"] = models.Food.objects.filter(pk=food_id).first()
        return initial


class ChildFoodProfileUpdate(CoreUpdateView):
    model = models.ChildFoodProfile
    template_name = "core/child_food_profile_form.html"
    permission_required = ("core.change_childfoodprofile",)
    form_class = forms.ChildFoodProfileForm
    success_url = reverse_lazy("core:child-food-profile-list")


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


class PumpingUpdate(CoreUpdateView):
    model = models.Pumping
    permission_required = ("core.change_pumping",)
    form_class = forms.PumpingForm
    success_url = reverse_lazy("core:pumping-list")
    success_message = _("%(model)s entry for %(child)s updated.")


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
        _prepare_timeline_context_data(context, date, user=self.request.user)
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
        name = (
            models.Timer.SLEEP_NAME
            if request.POST.get("kind") == "sleep"
            else None
        )
        instance = models.Timer.objects.create(user=request.user, name=name)
        # Find child from child pk in POST
        child_id = request.POST.get("child", False)
        child = models.Child.objects.get(pk=child_id) if child_id else None
        if child:
            instance.child = child
        # Add child relationship if there is only Child instance.
        elif models.Child.count() == 1:
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
