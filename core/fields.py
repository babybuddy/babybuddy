# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext as _


class NapStartMaxTimeField(forms.TimeField):
    def validate(self, value):
        from core.models import Sleep

        if value < Sleep.settings.nap_start_min:
            raise forms.ValidationError(
                _(
                    "Nap start max. value %(max)s must be greater than nap start min. value %(min)s."
                ),
                code="invalid_nap_start_max",
                params={"max": value, "min": Sleep.settings.nap_start_min},
            )


class NapStartMinTimeField(forms.TimeField):
    def validate(self, value):
        from core.models import Sleep

        if value > Sleep.settings.nap_start_max:
            raise forms.ValidationError(
                _(
                    "Nap start min. value %(min)s must be less than nap start max. value %(max)s."
                ),
                code="invalid_nap_start_min",
                params={"min": value, "max": Sleep.settings.nap_start_max},
            )
