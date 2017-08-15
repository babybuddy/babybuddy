# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.base import TemplateView


class IndexView(TemplateView):
    template_name = 'core/index.html'
