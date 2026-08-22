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


class OptionalPositiveIntegerValue(dbsettings.PositiveIntegerValue):
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


class LowStockSettings(dbsettings.Group):
    low_stock_threshold_days = OptionalPositiveIntegerValue(
        required=False,
        default=3,
        description=_("Low stock threshold (days)"),
        help_text=_(
            "Number of days of supply remaining before a diaper size is flagged "
            "as low stock on the dashboard."
        ),
    )


class FormulaClockSettings(dbsettings.Group):
    """User-overrideable opened-container clocks (audit C4, 2026-08-21).

    Defaults match the label-standard values the code hard-coded before:
    opened powder keeps for 1 month, opened ready-to-feed 48h in the
    fridge. Users who follow different label guidance (some RTF brands
    say 24h or 72h) can override site-wide.
    """

    powder_use_by_days = OptionalPositiveIntegerValue(
        required=False,
        default=31,
        description=_("Opened powder use-by (days)"),
        help_text=_(
            "How many days an opened powder container stays usable "
            "(label default: 1 month / 31 days). Caps at the printed "
            "expiry date regardless."
        ),
    )
    rtf_use_by_hours = OptionalPositiveIntegerValue(
        required=False,
        default=48,
        description=_("Opened ready-to-feed use-by (hours)"),
        help_text=_(
            "How many hours an opened ready-to-feed container stays "
            "usable in the fridge (label default: 48h)."
        ),
    )


class PumpingMethodSettings(dbsettings.Group):
    """Default pumping method (audit wave 3, 2026-08-21)."""

    default_method = dbsettings.StringValue(
        choices=[
            ("", "---------"),
            ("electric pump", "electric pump"),
            ("wearable pump", "wearable pump"),
            ("manual pump", "manual pump"),
            ("hand expression", "hand expression"),
        ],
        required=False,
        default="",
        description=_("Default pumping method"),
        help_text=_(
            "Pre-selected method on the Pumping add form. Blank keeps "
            "the field unselected."
        ),
    )


class DisplaySettings(dbsettings.Group):
    prev_word = dbsettings.StringValue(
        default="ago",
        choices=[("ago", "ago"), ("prior", "prior"), ("before", "before")],
        required=False,
        description=_("Previous-entry wording"),
        help_text=_(
            "Word displayed after the time gap in the 'Previous' column of "
            "activity list pages (e.g. '5 minutes ago')."
        ),
    )
