from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from babybuddy.mixins import PermissionRequiredMixin
from core.models import Child, DiaperChange
from django import forms
from django.urls import reverse, reverse_lazy


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


class CoreAddView(PermissionRequiredMixin, CreateView):
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        child = Child.objects.filter(slug__exact=context["view"].kwargs["slug"])[0]
        return context


class DiaperChangeForm(forms.ModelForm):
    class Meta:
        model = DiaperChange
        fields = ["time", "wet", "solid", "color", "amount", "notes", "tags"]
        widgets = {
            # "child": ChildRadioSelect(),
            # "time": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class DiaperChangeAdd(CoreAddView):
    template_name_suffix = "_mobile_form"
    model = DiaperChange
    permission_required = ("core.add_diaperchange",)
    form_class = DiaperChangeForm
    success_url = reverse_lazy("core:diaperchange-list")
