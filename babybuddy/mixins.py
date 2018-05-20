# -*- coding: utf-8 -*-
from django.contrib.auth.mixins import AccessMixin, PermissionRequiredMixin


class PermissionRequired403Mixin(PermissionRequiredMixin):
    """
    Raise an exception instead of redirecting to login.
    """
    raise_exception = True


class StaffOnlyMixin(AccessMixin):
    """
    Verify the current user is staff.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
