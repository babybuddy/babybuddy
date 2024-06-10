# -*- coding: utf-8 -*-
from django.views.generic.detail import DetailView

from babybuddy.mixins import PermissionRequiredMixin
from core import models

from . import graphs


class BMIChangeChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of BMI change over time.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/bmi_change.html"

    def get_context_data(self, **kwargs):
        context = super(BMIChangeChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        objects = models.BMI.objects.filter(child=child)
        if objects:
            context["html"], context["js"] = graphs.bmi_change(objects)
        return context


class ChildReportList(PermissionRequiredMixin, DetailView):
    """
    Listing of available reports for a child.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/report_list.html"


class DiaperChangeAmounts(PermissionRequiredMixin, DetailView):
    """
    Graph of diaper "amounts" - measurements of urine output.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/diaperchange_amounts.html"

    def get_context_data(self, **kwargs):
        context = super(DiaperChangeAmounts, self).get_context_data(**kwargs)
        child = context["object"]
        changes = models.DiaperChange.objects.filter(child=child, amount__gt=0)
        if changes and changes.count() > 0:
            context["html"], context["js"] = graphs.diaperchange_amounts(changes)
        return context


class DiaperChangeLifetimesChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of diaper "lifetimes" - time between diaper changes.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/diaperchange_lifetimes.html"

    def get_context_data(self, **kwargs):
        context = super(DiaperChangeLifetimesChildReport, self).get_context_data(
            **kwargs
        )
        child = context["object"]
        changes = models.DiaperChange.objects.filter(child=child)
        if changes and changes.count() > 1:
            context["html"], context["js"] = graphs.diaperchange_lifetimes(changes)
        return context


class DiaperChangeTypesChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of diaper changes by day and type.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/diaperchange_types.html"

    def get_context_data(self, **kwargs):
        context = super(DiaperChangeTypesChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        changes = models.DiaperChange.objects.filter(child=child)
        if changes:
            context["html"], context["js"] = graphs.diaperchange_types(changes)
        return context


class DiaperChangeIntervalsChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of diaper change intervals.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/diaperchange_intervals.html"

    def get_context_data(self, **kwargs):
        context = super(DiaperChangeIntervalsChildReport, self).get_context_data(
            **kwargs
        )
        child = context["object"]
        changes = models.DiaperChange.objects.filter(child=child)
        if changes:
            context["html"], context["js"] = graphs.diaperchange_intervals(changes)
        return context


class FeedingAmountsChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of daily feeding amounts over time.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/feeding_amounts.html"

    def __init__(self):
        super(FeedingAmountsChildReport, self).__init__()
        self.html = ""
        self.js = ""

    def get_context_data(self, **kwargs):
        context = super(FeedingAmountsChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        instances = models.Feeding.objects.filter(child=child)
        if instances:
            context["html"], context["js"] = graphs.feeding_amounts(instances)
        return context


class FeedingDurationChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of feeding durations over time.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/feeding_duration.html"

    def __init__(self):
        super(FeedingDurationChildReport, self).__init__()
        self.html = ""
        self.js = ""

    def get_context_data(self, **kwargs):
        context = super(FeedingDurationChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        instances = models.Feeding.objects.filter(child=child)
        if instances:
            context["html"], context["js"] = graphs.feeding_duration(instances)
        return context


class FeedingIntervalsChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of diaper change intervals.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/feeding_intervals.html"

    def get_context_data(self, **kwargs):
        context = super(FeedingIntervalsChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        instances = models.Feeding.objects.filter(child=child)
        if instances:
            context["html"], context["js"] = graphs.feeding_intervals(instances)
        return context


class FeedingPatternChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of feeding pattern.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/feeding_pattern.html"

    def __init__(self):
        super(FeedingPatternChildReport, self).__init__()
        self.html = ""
        self.js = ""

    def get_context_data(self, **kwargs):
        context = super(FeedingPatternChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        instances = models.Feeding.objects.filter(child=child).order_by("start")
        if instances:
            context["html"], context["js"] = graphs.feeding_pattern(instances)
        return context


class HeadCircumferenceChangeChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of head circumference change over time.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/head_circumference_change.html"

    def get_context_data(self, **kwargs):
        context = super(HeadCircumferenceChangeChildReport, self).get_context_data(
            **kwargs
        )
        child = context["object"]
        objects = models.HeadCircumference.objects.filter(child=child)
        if objects:
            (
                context["html"],
                context["js"],
            ) = graphs.head_circumference_change(objects)
        return context


class HeightChangeChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of height change over time.
    """

    def __init__(
        self, sex=None, target_url="reports:report-height-change-child"
    ) -> None:
        self.model = models.Child
        self.permission_required = ("core.view_child",)
        self.template_name = "reports/height_change.html"
        self.sex = sex
        self.target_url = target_url

    def get_context_data(self, **kwargs):
        context = super(HeightChangeChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        birthday = child.birth_date
        actual_heights = models.Height.objects.filter(child=child)
        percentile_heights = models.HeightPercentile.objects.filter(sex=self.sex)
        context["target_url"] = self.target_url
        if actual_heights:
            context["html"], context["js"] = graphs.height_change(
                actual_heights, percentile_heights, birthday
            )
        return context


class HeightChangeChildBoyReport(HeightChangeChildReport):
    def __init__(self):
        super(HeightChangeChildBoyReport, self).__init__(
            sex="boy", target_url="reports:report-height-change-child-boy"
        )


class HeightChangeChildGirlReport(HeightChangeChildReport):
    def __init__(self):
        super(HeightChangeChildGirlReport, self).__init__(
            sex="girl", target_url="reports:report-height-change-child-girl"
        )


class PumpingAmounts(PermissionRequiredMixin, DetailView):
    """
    Graph of pumping milk amounts collected.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/pumping_amounts.html"

    def get_context_data(self, **kwargs):
        context = super(PumpingAmounts, self).get_context_data(**kwargs)
        child = context["object"]
        changes = models.Pumping.objects.filter(child=child)
        if changes and changes.count() > 0:
            context["html"], context["js"] = graphs.pumping_amounts(changes)
        return context


class SleepPatternChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of sleep pattern comparing sleep to wake times by day.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/sleep_pattern.html"

    def __init__(self):
        super(SleepPatternChildReport, self).__init__()
        self.html = ""
        self.js = ""

    def get_context_data(self, **kwargs):
        context = super(SleepPatternChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        instances = models.Sleep.objects.filter(child=child).order_by("start")
        if instances:
            context["html"], context["js"] = graphs.sleep_pattern(instances)
        return context


class SleepTotalsChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of total sleep by day.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/sleep_totals.html"

    def __init__(self):
        super(SleepTotalsChildReport, self).__init__()
        self.html = ""
        self.js = ""

    def get_context_data(self, **kwargs):
        context = super(SleepTotalsChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        instances = models.Sleep.objects.filter(child=child).order_by("start")
        if instances:
            context["html"], context["js"] = graphs.sleep_totals(instances)
        return context


class TemperatureChangeChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of temperature change over time.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/temperature_change.html"

    def get_context_data(self, **kwargs):
        context = super(TemperatureChangeChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        objects = models.Temperature.objects.filter(child=child)
        if objects:
            context["html"], context["js"] = graphs.temperature_change(objects)
        return context


class TummyTimeDurationChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of tummy time durations over time.
    """

    model = models.Child
    permission_required = ("core.view_child",)
    template_name = "reports/tummytime_duration.html"

    def __init__(self):
        super(TummyTimeDurationChildReport, self).__init__()
        self.html = ""
        self.js = ""

    def get_context_data(self, **kwargs):
        context = super(TummyTimeDurationChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        instances = models.TummyTime.objects.filter(child=child)
        if instances:
            context["html"], context["js"] = graphs.tummytime_duration(instances)
        return context


class WeightChangeChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of weight change over time.
    """

    def __init__(
        self, sex=None, target_url="reports:report-weight-change-child"
    ) -> None:
        self.model = models.Child
        self.permission_required = ("core.view_child",)
        self.template_name = "reports/weight_change.html"
        self.sex = sex
        self.target_url = target_url

    def get_context_data(self, **kwargs):
        context = super(WeightChangeChildReport, self).get_context_data(**kwargs)
        child = context["object"]
        birthday = child.birth_date
        actual_weights = models.Weight.objects.filter(child=child)
        percentile_weights = models.WeightPercentile.objects.filter(sex=self.sex)
        context["target_url"] = self.target_url
        if actual_weights:
            context["html"], context["js"] = graphs.weight_change(
                actual_weights, percentile_weights, birthday
            )
        return context


class WeightChangeChildBoyReport(WeightChangeChildReport):
    def __init__(self):
        super(WeightChangeChildBoyReport, self).__init__(
            sex="boy", target_url="reports:report-weight-change-child-boy"
        )


class WeightChangeChildGirlReport(WeightChangeChildReport):
    def __init__(self):
        super(WeightChangeChildGirlReport, self).__init__(
            sex="girl", target_url="reports:report-weight-change-child-girl"
        )
