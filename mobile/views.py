from django.views.generic.detail import DetailView

from babybuddy.mixins import PermissionRequiredMixin
from core.models import Child

class MobileChildDashboard(PermissionRequiredMixin, DetailView):
    model = Child
    permission_required = ("core.view_child",)
    template_name = "child.html"
    context_object_name = "child"
    
