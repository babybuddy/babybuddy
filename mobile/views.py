from django.views.generic.detail import DetailView

from babybuddy.mixins import PermissionRequiredMixin
from core.models import Child
from core.forms import DiaperChangeForm
from core.views import DiaperChangeAdd
from mobile.constants import activities
from django.urls import reverse


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
    fieldsets = {"choices": ["wet", "solid"], "required": ["time"], "hidden": ["child"]}


class MobileDiaperChangeAdd(DiaperChangeAdd):
    template_name_suffix = "_mobile_form"
    form_class = MobileDiaperChangeForm

    def get_success_url(self):
        return reverse("mobile:mobile-dashboard-child", kwargs=self.kwargs)
