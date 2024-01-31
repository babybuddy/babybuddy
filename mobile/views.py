from django.views.generic.detail import DetailView

from babybuddy.mixins import PermissionRequiredMixin
from core.models import Child
from core.forms import DiaperChangeForm, BottleFeedingForm, PumpingForm
from core.views import DiaperChangeAdd, BottleFeedingAdd, PumpingAdd
from django.urls import reverse
from mobile.constants import activities


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


class GenericMobileFormMixin:
    template_name_field = "template_name"
    template_name = "generic_mobile_form.html"

    def get_success_url(self):
        return reverse("mobile:mobile-dashboard-child", args=[self.object.child.slug])


class MobileDiaperChangeAdd(GenericMobileFormMixin, DiaperChangeAdd):
    pass


class MobileBottleFeedingAdd(GenericMobileFormMixin, BottleFeedingAdd):
    pass


class MobilePumpingAdd(GenericMobileFormMixin, PumpingAdd):
    pass
