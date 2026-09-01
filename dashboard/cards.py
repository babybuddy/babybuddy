# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _

from core.models import ActivityType

# Cards which are always available on a child dashboard, in the order that they
# are rendered by "dashboard/child.html". The identifiers are stored in each
# user's settings, so they must remain stable.
BUILT_IN_CARDS = [
    ("timer_list", _("Timers")),
    ("feeding_last", _("Last Feeding")),
    ("diaperchange_last", _("Last Diaper Change")),
    ("pumping_last", _("Last Pumping")),
    ("pumping_recent", _("Recent Pumpings")),
    ("sleep_last", _("Last Sleep")),
    ("medication_last", _("Last Medication")),
    ("feeding_last_method", _("Last Feeding Method")),
    ("feeding_recent", _("Recent Feedings")),
    ("statistics", _("Statistics")),
    ("sleep_recent", _("Recent Sleep")),
    ("sleep_naps_day", _("Today's Naps")),
    ("tummytime_day", _("Today's Tummy Time")),
    ("diaperchange_types", _("Diaper Changes")),
    ("breastfeeding", _("Breastfeeding")),
]

ACTIVITY_CARD_PREFIX = "activity:"


def get_hidden_card_ids(user):
    """
    Get the set of dashboard card identifiers hidden by a user.
    :param user: a User instance.
    :returns: a set of card identifiers.
    """
    settings = getattr(user, "settings", None)
    return set(getattr(settings, "dashboard_hidden_cards", None) or [])


def get_active_activity_types():
    """
    Get all ActivityType instances which may have a dashboard card.
    :returns: an ActivityType queryset.
    """
    return ActivityType.objects.filter(active=True)


def get_card_choices():
    """
    Get all available dashboard cards, including one card per active
    ActivityType instance.
    :returns: a list of (identifier, label) tuples.
    """
    choices = list(BUILT_IN_CARDS)
    choices += [
        (activity_type.card_id, activity_type.name)
        for activity_type in get_active_activity_types()
    ]
    return choices


def get_visible_card_ids(user):
    """
    Get the dashboard card identifiers a user has *not* hidden.
    :param user: a User instance.
    :returns: a set of card identifiers.
    """
    hidden = get_hidden_card_ids(user)
    return {card_id for card_id, _label in get_card_choices() if card_id not in hidden}


def get_visible_activity_types(user):
    """
    Get the ActivityType instances with a dashboard card visible to a user.
    :param user: a User instance.
    :returns: a list of ActivityType instances.
    """
    hidden = get_hidden_card_ids(user)
    return [
        activity_type
        for activity_type in get_active_activity_types()
        if activity_type.card_id not in hidden
    ]
