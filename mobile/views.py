from django.views.generic.detail import DetailView

from babybuddy.mixins import PermissionRequiredMixin
from core.models import Child
from core.forms import DiaperChangeForm, BottleFeedingForm
from core.views import DiaperChangeAdd, BottleFeedingAdd
from mobile.constants import activities
from django.urls import reverse
from django.forms import RadioSelect, widgets


class MobileChildDashboard(PermissionRequiredMixin, DetailView):
    model = Child
    permission_required = ("core.view_child",)
    template_name = "child.html"
    context_object_name = "child"


class MobileChildDashboard(PermissionRequiredMixin, DetailView):
    model = Child
    permission_required = ("core.view_child",)
    template_name = "child.html"
    context_object_name = "child"


class MobileDiaperChangeForm(DiaperChangeForm):
    theme = activities["changes"]
    fieldsets = {"choices": ["wet", "solid"], "required": ["time", "child"]}


class MobileDiaperChangeAdd(DiaperChangeAdd):
    template_name_suffix = "_mobile_form"
    form_class = MobileDiaperChangeForm

    def get_success_url(self):
        return reverse("mobile:mobile-dashboard-child", args=[self.object.child.slug])


class MobileBottleFeedingForm(BottleFeedingForm):
    theme = activities["bottle"]
    fieldsets = {
        "choices": ["type"],
        "required": ["child", "start", "amount"],
    }


class MobileBottleFeedingAdd(BottleFeedingAdd):
    template_name_suffix = "_mobile_form"
    form_class = MobileBottleFeedingForm

    def get_success_url(self):
        return reverse("mobile:mobile-dashboard-child", args=[self.object.child.slug])
