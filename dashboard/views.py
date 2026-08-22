# -*- coding: utf-8 -*-
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView

from babybuddy.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.models import Child
from core import models as core_models


class Dashboard(LoginRequiredMixin, TemplateView):
    # TODO: Use .card-deck in this template once BS4 is finalized.
    template_name = "dashboard/dashboard.html"

    # Show the overall dashboard or a child dashboard if one Child instance.
    def get(self, request, *args, **kwargs):
        children = Child.objects.count()
        if children == 0:
            return HttpResponseRedirect(reverse("babybuddy:welcome"))
        elif children == 1:
            return HttpResponseRedirect(
                reverse("dashboard:dashboard-child", args={Child.objects.first().slug})
            )
        return super(Dashboard, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        context["objects"] = Child.objects.all().order_by(
            "last_name", "first_name", "id"
        )
        return context


class ChildDashboard(PermissionRequiredMixin, DetailView):
    model = Child
    permission_required = ("core.view_child",)
    template_name = "dashboard/child.html"


class CustomizeCards(LoginRequiredMixin, View):
    """Toggle dashboard card visibility AND reorder cards in one place.

    This view merges the former separate "customize" (visibility) and
    "reorder" pages into a single drag-and-drop interface. The combined
    page supports both desktop (mouse) and mobile (touch) reordering.

    It also handles the breast_activity_time_mode setting (start vs end).
    """

    DASHBOARD_CARDS = [
        {"name": "feeding_last", "label": "Last Feeding", "description": "Most recent feeding entry", "category": "Feeding"},
        {"name": "feeding_consumption", "label": "Recent Consumption", "description": "Rolling 3h/6h/12h feeding totals", "category": "Feeding"},
        {"name": "feeding_last_method", "label": "Feeding Methods", "description": "Recent feeding methods breakdown", "category": "Feeding"},
        {"name": "feeding_recent", "label": "Recent Feeding", "description": "Daily feeding totals for past week", "category": "Feeding"},
        {"name": "breastfeeding", "label": "Breastfeeding", "description": "7-day breastfeeding stats", "category": "Feeding"},
        {"name": "breast_activity", "label": "Last Breast Activity", "description": "Most recent of breastfeeding or pumping", "category": "Feeding"},
        {"name": "pumping_last", "label": "Last Pumping", "description": "Most recent pumping session", "category": "Pumping & Milk"},
        {"name": "pumping_recent", "label": "Recent Pumping", "description": "7-day pumping totals", "category": "Pumping & Milk"},
        {"name": "feed_inventory", "label": "Milk Inventory", "description": "Stored milk by type and location", "category": "Pumping & Milk"},
        {"name": "active_bottles", "label": "Active Bottles", "description": "Prepared bottles with use-by countdowns", "category": "Feeding"},
        {"name": "diaperchange_last", "label": "Last Diaper Change", "description": "Most recent diaper change", "category": "Diaper"},
        {"name": "diaperchange_types", "label": "Diaper Change Types", "description": "7-day diaper breakdown by type", "category": "Diaper"},
        {"name": "low_stock", "label": "Diaper Stock Alerts", "description": "Diaper sizes running low", "category": "Diaper"},
        {"name": "sleep_last", "label": "Last Sleep", "description": "Most recent sleep entry", "category": "Sleep"},
        {"name": "sleep_recent", "label": "Recent Sleep", "description": "Daily sleep totals for past week", "category": "Sleep"},
        {"name": "sleep_naps_day", "label": "Naps", "description": "Today's nap count and duration", "category": "Sleep"},
        {"name": "spitup", "label": "Spit-Up", "description": "24h spit-up count and recent episodes", "category": "Health & Notes"},
        {"name": "medication_last", "label": "Last Medication", "description": "Most recent medication dose", "category": "Health & Notes"},
        {"name": "notes_recent", "label": "Recent Notes", "description": "Last 4 notes", "category": "Health & Notes"},
        {"name": "tummytime_day", "label": "Tummy Time", "description": "Today's tummy time", "category": "Health & Notes"},
        {"name": "timer_list", "label": "Timers", "description": "Active timers", "category": "System"},
        {"name": "statistics", "label": "Statistics", "description": "Summary statistics", "category": "System"},
    ]

    CARD_CATEGORIES = ["Feeding", "Pumping & Milk", "Diaper", "Sleep", "Health & Notes", "System"]

    def _get_ordered_cards(self, config):
        """Build the ordered card list from saved config + defaults."""
        saved_order = config.get("_card_order", [])
        seen = set()
        cards = []

        # Ordered cards first
        for name in saved_order:
            for card in self.DASHBOARD_CARDS:
                if card["name"] == name and name not in seen:
                    cards.append({
                        **card,
                        "visible": config.get(name, {}).get("visible", True),
                    })
                    seen.add(name)
                    break

        # Then any remaining defaults not in saved order
        for card in self.DASHBOARD_CARDS:
            if card["name"] not in seen:
                cards.append({
                    **card,
                    "visible": config.get(card["name"], {}).get("visible", True),
                })

        return cards

    def _get_categorized_cards(self, config):
        """Group cards by category for the template.
        Returns a list of (category, cards) tuples.
        Also computes per-category visibility state.
        """
        all_cards = self._get_ordered_cards(config)
        result = []
        for cat in self.CARD_CATEGORIES:
            cat_cards = [c for c in all_cards if c.get("category") == cat]
            all_on = all(c["visible"] for c in cat_cards) if cat_cards else True
            result.append({
                "name": cat,
                "cards": cat_cards,
                "all_visible": all_on,
            })
        return result

    def get(self, request, *args, **kwargs):
        config = request.user.settings.dashboard_card_config or {}
        cards = self._get_ordered_cards(config)
        child = core_models.Child.objects.first()
        breast_activity_mode = getattr(
            request.user.settings, "breast_activity_time_mode", "end"
        )
        categories = self._get_categorized_cards(config)
        return render(request, "dashboard/customize_cards.html", {
            "cards": cards,
            "categories": categories,
            "object": child,
            "breast_activity_mode": breast_activity_mode,
        })

    def post(self, request, *args, **kwargs):
        config = {}
        # Save visibility for each card
        for card in self.DASHBOARD_CARDS:
            visible = request.POST.get(f"card_{card['name']}") == "on"
            config[card["name"]] = {"visible": visible}
        # Save card order from the hidden field
        order = request.POST.getlist("card_order")
        order_clean = [v.strip() for v in order if v.strip()]
        config["_card_order"] = order_clean

        settings = request.user.settings
        settings.dashboard_card_config = config

        # Save breast_activity_time_mode
        mode = request.POST.get("breast_activity_time_mode", "end")
        if mode in ("start", "end"):
            settings.breast_activity_time_mode = mode

        settings.save()

        messages.success(request, "Dashboard cards updated.")
        child = core_models.Child.objects.first()
        return redirect("dashboard:dashboard-child", slug=child.slug)


class ReorderCards(LoginRequiredMixin, View):
    """Backward-compatible redirect to the combined CustomizeCards page.

    The old separate reorder page is now merged into CustomizeCards.
    This view preserves the old URL so existing links/bookmarks still work.
    """

    def get(self, request, *args, **kwargs):
        return redirect("dashboard:dashboard-cards")

    def post(self, request, *args, **kwargs):
        return redirect("dashboard:dashboard-cards")
