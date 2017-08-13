# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms import fields, widgets
from djng.styling.bootstrap3.forms import Bootstrap3Form


class BabyForm(Bootstrap3Form):
    use_required_attribute = False

    first_name = fields.CharField(
        label='First name',
        min_length=3,
        max_length=20)

    last_name = fields.RegexField(
        r'^[A-Z][a-z -]?',
        label='Last name',
        error_messages={'invalid': 'Last names shall start in upper case'})

    birth_date = fields.DateField(
        label='Date of birth',
        widget=widgets.DateInput(attrs={'validate-date': '^(\d{4})-(\d{1,2})-(\d{1,2})$'}),
        help_text='Allowed date format: yyyy-mm-dd')
