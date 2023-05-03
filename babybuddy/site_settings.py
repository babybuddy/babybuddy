# -*- coding: utf-8 -*-
from datetime import time

from django.utils.translation import gettext_lazy as _

import dbsettings

from .widgets import TimeInput


class NapSettings(dbsettings.Group):
    nap_start_min = dbsettings.TimeValue(
        default=time(6),
        description=_("Default minimum nap start time"),
        help_text=_(
            "The minimum default time that a sleep entry is consider a nap. If set the "
            "nap property will be preselected if the start time is within the bounds."
        ),
        widget=TimeInput,
    )
    nap_start_max = dbsettings.TimeValue(
        default=time(18),
        description=_("Default maximum nap start time"),
        help_text=_(
            "The maximum default time that a sleep entry is consider a nap. If set the "
            "nap property will be preselected if the start time is within the bounds."
        ),
        widget=TimeInput,
    )
