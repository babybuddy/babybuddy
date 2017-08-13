# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse_lazy
from django.views.generic.edit import FormView

from core.forms import BabyForm


class BabyFormView(FormView):
    template_name = 'baby-form.html'
    form_class = BabyForm
    success_url = reverse_lazy('form_data_valid')
