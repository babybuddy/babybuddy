# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms

from .models import Child


class ChildAddForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['first_name', 'last_name', 'birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={
                'class': 'datepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_birth_date',
            }),
        }
