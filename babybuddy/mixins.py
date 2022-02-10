# -*- coding: utf-8 -*-
from django.contrib.auth.mixins import (
    AccessMixin,
    LoginRequiredMixin as LoginRequiredMixInBase,
    PermissionRequiredMixin as PermissionRequiredMixinBase,
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


@method_decorator(never_cache, name="dispatch")
class LoginRequiredMixin(LoginRequiredMixInBase):
    pass


@method_decorator(never_cache, name="dispatch")
class PermissionRequiredMixin(PermissionRequiredMixinBase):
    login_url = "/login"


@method_decorator(never_cache, name="dispatch")
class StaffOnlyMixin(AccessMixin):
    """
    Verify the current user is staff.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
