# -*- coding: utf-8 -*-
from datetime import time

from django.utils.translation import gettext_lazy as _

import dbsettings

from django.forms.fields import BooleanField
from core.fields import NapStartMaxTimeField, NapStartMinTimeField
from .widgets import TimeInput
from django.forms.widgets import CheckboxInput


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


class FeedingDiffEndValue(dbsettings.BooleanValue):
    field = BooleanField


class ContinuationThresholdValue(dbsettings.PositiveIntegerValue):
    """
    Optional positive integer that falls back to its default when unset.

    ``required=False`` keeps the site settings form valid on partial POSTs
    (upstream tests submit only some fields), and ``to_python`` falls back
    to the default so a blank value never poisons the stored setting.
    """

    def to_python(self, value):
        if self.meaningless(value):
            return self.default
        try:
            return int(value)
        except (TypeError, ValueError):
            return self.default


class FeedingSettings(dbsettings.Group):
    feeding_diff_end = FeedingDiffEndValue(
        required=False,
        default=False,
        description=_("Time diff between feedings based on end"),
        help_text=_(
            "Use feeding end instead of start time for displaying time between feedings"
        ),
        widget=CheckboxInput,
    )
    continuation_threshold_minutes = ContinuationThresholdValue(
        required=False,
        default=30,
        description=_("Continuation auto-link threshold (minutes)"),
        help_text=_(
            "When logging a new feeding, the most recent feeding is pre-selected "
            "as a continuation if it ended within this many minutes of the new "
            "feeding's start. Also used by the Recent Consumption card to group "
            "feedings into sessions."
        ),
    )
