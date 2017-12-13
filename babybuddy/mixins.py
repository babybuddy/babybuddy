# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import AccessMixin


class StaffOnlyMixin(AccessMixin):
    """
    Verify the current user is staff.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
