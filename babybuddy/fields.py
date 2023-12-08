# -*- coding: utf-8 -*-
from django import forms

from babybuddy.widgets import StartEndDateTimeInput


class StartEndDateField(forms.MultiValueField):
    widget = StartEndDateTimeInput

    def __init__(self, *args, **kwargs):
        super(StartEndDateField, self).__init__(
            [forms.DateTimeField(), forms.DateTimeField()], *args, **kwargs
        )

    def compress(self, data_list):
        return " ".join(data_list)
