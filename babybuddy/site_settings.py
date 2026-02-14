# -*- coding: utf-8 -*-
from datetime import time

from django.utils.translation import gettext_lazy as _

import dbsettings

from core.fields import NapStartMaxTimeField, NapStartMinTimeField
from .widgets import TimeInput


class NapStartMaxTimeValue(dbsettings.TimeValue):
    field = NapStartMaxTimeField


class NapStartMinTimeValue(dbsettings.TimeValue):
    field = NapStartMinTimeField


class NapSettings(dbsettings.Group):
    nap_start_min = NapStartMinTimeValue(
        default=time(6),
        description=_("Default minimum nap start time"),
        help_text=_(
            "The minimum default time that a sleep entry is consider a nap. If set the nap property will be preselected if the start time is within the bounds."
        ),
        widget=TimeInput,
    )
    nap_start_max = NapStartMaxTimeValue(
        default=time(18),
        description=_("Default maximum nap start time"),
        help_text=_(
            "The maximum default time that a sleep entry is consider a nap. If set the nap property will be preselected if the start time is within the bounds."
        ),
        widget=TimeInput,
    )
