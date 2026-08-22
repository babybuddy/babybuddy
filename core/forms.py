# -*- coding: utf-8 -*-
from django import forms
from django.db.models import Q
from django.forms import widgets
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from taggit.forms import TagField

from babybuddy.widgets import DateInput, DateTimeInput, TimeInput
from core import models
from core.models import Timer
from core.widgets import (
    TagsEditor,
    ChildRadioSelect,
    PillRadioSelect,
    RequiredPillRadioSelect,
    PillCheckboxSelect,
)


def set_initial_values(kwargs, form_type):
    """
    Sets initial value for add forms based on provided kwargs.

    :param kwargs: Keyword arguments.
    :param form_type: Class of the type of form being initialized.
    :return: Keyword arguments with updated "initial" values.
    """

    # Never update initial values for existing instance (e.g. edit operation).
    if kwargs.get("instance", None):
        return kwargs

    # Add the "initial" kwarg if it does not already exist.
    if not kwargs.get("initial"):
        kwargs.update(initial={})

    # Set Child based on `child` kwarg or single Chile database.
    child_slug = kwargs.get("child", None)
    if child_slug:
        kwargs["initial"].update(
            {
                "child": models.Child.objects.filter(slug=child_slug).first(),
            }
        )
    elif models.Child.objects.count() == 1:
        # Do not trust the cached Child.count() here: bulk/cascade deletes
        # bypass Child.save()/delete() so the cache can go stale (cache=3,
        # DB=1 observed), silently breaking the single-child default.
        kwargs["initial"].update({"child": models.Child.objects.first()})

    # Set start and end time based on Timer from `timer` kwarg.
    timer_id = kwargs.get("timer", None)
    if timer_id:
        try:
            timer = models.Timer.objects.get(id=timer_id)
            kwargs["initial"].update(
                {"timer": timer, "start": timer.start, "end": timezone.now()}
            )
        except Timer.DoesNotExist:
            pass

    # Set type and method values for Feeding instance based on last feed
    # of the SAME category. Each form type gets its own independent defaults
    # so switching between Breast/Bottle/Solid forms does not bleed values.
    feeding_form_types = (
        FeedingForm,
        BottleFeedingForm,
        BreastFeedingForm,
        SolidFeedingForm,
    )
    if form_type in feeding_form_types and "child" in kwargs["initial"]:
        child = kwargs["initial"]["child"]

        if form_type == BreastFeedingForm:
            last_feeding = (
                models.Feeding.objects.filter(
                    child=child,
                    method__in=["left breast", "right breast", "both breasts"],
                )
                .order_by("end")
                .last()
            )
            if last_feeding:
                kwargs["initial"].update(
                    {"type": last_feeding.type, "method": last_feeding.method}
                )
        elif form_type == BottleFeedingForm:
            last_feeding = (
                models.Feeding.objects.filter(child=child, method="bottle")
                .order_by("end")
                .last()
            )
            if last_feeding:
                kwargs["initial"].update({"type": last_feeding.type})
        elif form_type == SolidFeedingForm:
            last_feeding = (
                models.Feeding.objects.filter(
                    child=child,
                    method__in=["parent fed", "self fed"],
                )
                .order_by("end")
                .last()
            )
            if last_feeding:
                kwargs["initial"].update({"method": last_feeding.method})
        elif form_type == FeedingForm:
            last_feeding = (
                models.Feeding.objects.filter(child=child).order_by("end").last()
            )
            if last_feeding:
                last_method = last_feeding.method
                last_feed_args = {"type": last_feeding.type}
                if last_method not in ["left breast", "right breast"]:
                    last_feed_args["method"] = last_method
                kwargs["initial"].update(last_feed_args)

    # Carry over diaper size and brand from last change.
    if form_type == DiaperChangeForm and "child" in kwargs["initial"]:
        last_change = (
            models.DiaperChange.objects.filter(child=kwargs["initial"]["child"])
            .order_by("time")
            .last()
        )
        if last_change:
            carry = {}
            if last_change.diaper_size:
                carry["diaper_size"] = last_change.diaper_size
            if last_change.diaper_brand:
                carry["diaper_brand"] = last_change.diaper_brand
            kwargs["initial"].update(carry)

    # Set default "nap" value for Sleep instances.
    if form_type == SleepForm and "nap" not in kwargs["initial"]:
        try:
            start = timezone.localtime(kwargs["initial"]["start"]).time()
        except KeyError:
            start = timezone.localtime().time()
        nap = (
            models.Sleep.settings.nap_start_min
            <= start
            <= models.Sleep.settings.nap_start_max
        )
        kwargs["initial"].update({"nap": nap})

    # Carry timer name into notes field if present.
    timer_name = kwargs.get("timer_name")
    if timer_name and "notes" not in kwargs.get("initial", {}):
        kwargs["initial"].update({"notes": str(timer_name)})

    # Remove custom kwargs, so they do not interfere with `super` calls.
    for key in ["child", "timer", "timer_name"]:
        try:
            kwargs.pop(key)
        except KeyError:
            pass

    return kwargs


class CoreModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Set `timer_id` so the Timer can be stopped in the `save` method.
        self.timer_id = kwargs.get("timer", None)
        kwargs = set_initial_values(kwargs, type(self))
        super(CoreModelForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        # If `timer_id` is present, stop the Timer.
        instance = super(CoreModelForm, self).save(commit=False)
        if self.timer_id:
            timer = models.Timer.objects.get(id=self.timer_id)
            timer.stop()
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    @property
    def hydrated_fielsets(self):
        # for some reason self.fields returns defintions and not bound fields
        # so until i figure out a better way we can just create a dict here
        # https://github.com/django/django/blob/main/django/forms/forms.py#L52

        bound_field_dict = {}
        for field in self:
            bound_field_dict[field.name] = field

        hydrated_fieldsets = []

        for fieldset in self.fieldsets:
            hyrdrated_fieldset = {
                "layout": fieldset.get("layout", "default"),
                "layout_attrs": fieldset.get("layout_attrs", {}),
                "fields": [],
            }
            for field_name in fieldset["fields"]:
                hyrdrated_fieldset["fields"].append(bound_field_dict[field_name])

            hydrated_fieldsets.append(hyrdrated_fieldset)

        return hydrated_fieldsets


class TaggableModelForm(forms.ModelForm):
    tags = TagField(
        label=_("Tags"),
        widget=TagsEditor,
        required=False,
        strip=True,
        help_text=_(
            "Click on the tags to add (+) or remove (-) tags or use the text editor to create new tags."
        ),
    )


class BMIForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "bmi", "date"],
            "layout": "required",
        },
        {"fields": ["notes"], "layout": "advanced"},
    ]

    class Meta:
        model = models.BMI
        fields = ["child", "bmi", "date", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "date": DateInput(),
            "previous_feeding": forms.Select(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class BottleFeedingForm(CoreModelForm, TaggableModelForm):
    nipple_size = forms.ChoiceField(
        choices=[("", _("---------"))],
        required=False,
        widget=PillRadioSelect(),
    )

    # ProductLine dropdowns — not model fields, translated in clean()
    bottle_product = forms.ChoiceField(
        required=False,
        label=_("Bottle"),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_bottle_product"}),
    )
    # B7 (2026-08-21): the free formula_product dropdown is removed —
    # formula identity comes from the formula_source picker (inventory
    # or prepared bottle) or nothing. formula_brand stays on the model
    # for history; legacy rows keep their brand.
    # Milk Inventory item this feeding consumes (decrements amount_remaining)
    feed_inventory = forms.ModelChoiceField(
        queryset=models.FeedInventory.objects.none(),
        required=False,
        label=_("Milk inventory item"),
        help_text=_(
            "Optional. Select a Milk Inventory item to decrement its "
            "remaining amount by this feeding's amount."
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    # Formula source picker — one dropdown, three optgroups (spec
    # §Feeding form integration): prepared bottles, opened RTF, opened
    # powder. Not a model field; translated to prepared_feed /
    # formula_stock FKs in clean().
    formula_source = forms.ChoiceField(
        required=False,
        label=_("Formula source"),
        help_text=_(
            "Optional. Prepared bottle, opened ready-to-feed, or opened "
            "powder. Derives the brand and decrements the source."
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    # T6 inline prep — optional "amount mixed" capture when the source is
    # a powder pool. Blank or mixed == fed: direct-pool behavior (no unit,
    # grams for fed only). Mixed > fed: creates a PreparedFeed unit at
    # save time (pool decrements grams for the FULL mixed amount; the unit
    # carries the leftover ml + T4 clocks).
    amount_mixed = forms.FloatField(
        required=False,
        min_value=0,
        label=_("Amount mixed (ml)"),
        help_text=_(
            "Optional. For powder sources: how much you mixed. More than "
            "fed creates a prepared bottle for the leftover."
        ),
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "any",
            "id": "id_amount_mixed",
        }),
    )

    fieldsets = [
        {
            "fields": ["child", "type", "start", "end", "amount", "amount_unit"],
            "layout": "required",
        },
        {
            "fields": [
                "bottle_product",
                "nipple_size",
                "feed_inventory",
                "formula_source",
                "amount_mixed",
            ],
            "layout": "bottle_attrs",
        },
        {"fields": ["previous_feeding", "notes", "tags"], "layout": "advanced"},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Quick-entry: an end time is rarely known for a bottle feeding
        # logged after the fact, so leave it blank and default to start
        # in clean()/save() (restores fix b3072001, lost in the Aug 5
        # dev rebuild).
        self.fields["end"].required = False

        # Filter choices to bottle-relevant options only
        self.fields["type"].choices = [
            ("breast milk", _("Breast milk")),
            ("formula", _("Formula")),
            ("fortified breast milk", _("Fortified breast milk")),
        ]

        def _feeding_label(f):
            local_start = timezone.localtime(f.start)
            local_end = timezone.localtime(f.end)
            if local_start.strftime("%m/%d") == local_end.strftime("%m/%d"):
                label = f"{local_start.strftime('%m/%d %I:%M %p')} - {local_end.strftime('%I:%M %p')} — {f.get_method_display()}"
            else:
                label = f"{local_start.strftime('%m/%d %I:%M %p')} - {local_end.strftime('%m/%d %I:%M %p')} — {f.get_method_display()}"
            if f.amount:
                label += f" ({f.amount}ml)"
            return label

        # Build previous_feeding choices:
        # - New record: show 15 most recent feedings
        # - Existing record: show feedings within +/-6h of this feeding's start
        pf_choices = [("", _("---------"))]
        if self.instance and self.instance.pk and self.instance.start:
            ref_time = self.instance.start
            window = timezone.timedelta(hours=6)
            feedings = list(
                models.Feeding.objects.filter(
                    end__range=(ref_time - window, ref_time + window)
                ).order_by("-end")
            )
            if self.instance.previous_feeding_id:
                selected_id = self.instance.previous_feeding_id
                if not any(f.id == selected_id for f in feedings):
                    feedings.insert(0, self.instance.previous_feeding)
            for f in feedings:
                if f.pk == self.instance.pk:
                    continue
                pf_choices.append((f.id, _feeding_label(f)))
        else:
            for f in models.Feeding.objects.order_by("-end")[:15]:
                pf_choices.append((f.id, _feeding_label(f)))

        self.fields["previous_feeding"].choices = pf_choices

        # Populate bottle_product dropdown from OWNED equipment (bottles).
        # Equipment is the source of truth for what can actually be used;
        # ProductLine is just the master catalog.
        bottle_choices = [("", _("---------"))]
        seen = set()
        for eq in models.EquipmentItem.objects.filter(
            product_line__item_type="bottles"
        ).select_related("product_line").order_by(
            "product_line__brand", "product_line__line"
        ):
            pl = eq.product_line
            key = (pl.brand, pl.line)
            if key in seen:
                continue
            seen.add(key)
            bottle_choices.append((f"{pl.brand}||{pl.line}", str(pl)))
        self.fields["bottle_product"].choices = bottle_choices

        # Populate feed_inventory dropdown from Milk Inventory items with
        # remaining amount > 0 (plus the currently linked item so edits
        # don't lose the selection)
        inventory_qs = models.FeedInventory.objects.filter(amount_remaining__gt=0)
        if self.instance and self.instance.feed_inventory_id:
            inventory_qs = inventory_qs | models.FeedInventory.objects.filter(
                pk=self.instance.feed_inventory_id
            )
        self.fields["feed_inventory"].queryset = inventory_qs.order_by("-expressed_at")
        self.fields["feed_inventory"].label_from_instance = lambda obj: (
            f"{obj} — {obj.amount_remaining or 0:g}ml remaining"
        )

        # Formula source picker: one dropdown, three optgroups.
        # Prepared bottles decrement ml directly; RTF/powder decrement
        # their pool. Values encode kind+pk ("prepared:3", "rtf:5",
        # "powder:7") so clean() can rebuild the FKs without extra
        # queries.
        prepared = list(
            models.PreparedFeed.objects.filter(status="active")
            .filter(
                Q(amount_remaining__gt=0)
                | Q(amount_remaining__isnull=True, amount__gt=0)
            )
            .order_by("-prepared_at")[:30]
        )
        # T4 no-grace rule (CDC): an expired bottle is not feedable.
        # use_by_info() computes the live clock; danger badge = past the
        # use-by bound. Drop those here so the picker only offers units
        # still inside their window.
        prepared = [
            pf
            for pf in prepared
            if pf.use_by_info()["css_class"] != "text-bg-danger"
        ]
        # A2 (2026-08-21): reserves are never decrementable — exclude
        # from the picker entirely (matches the auto-pick + diaper-side
        # convention). Using a reserve = uncheck Reserve on the pool.
        rtf = list(
            models.FormulaStock.objects.filter(
                form="rtf", opened_at__isnull=False
            )
            .filter(ml_remaining__gt=0)
            .exclude(is_reserve=True)
            .order_by("-drain_priority", "opened_at")
        )
        powder = list(
            models.FormulaStock.objects.filter(
                form="powder", opened_at__isnull=False
            )
            .filter(grams_remaining__gt=0)
            .exclude(is_reserve=True)
            .order_by("-drain_priority", "opened_at")
        )

        def _prepared_label(pf):
            rem = (
                pf.amount_remaining
                if pf.amount_remaining is not None
                else pf.amount
            )
            brand = (
                pf.source_pool.product_line.brand
                if pf.source_pool
                else None
            )
            name = f"#{pf.pk}"
            if brand:
                name = f"{brand} #{pf.pk}"
            return f"{name} — {rem or 0:g}ml remaining ({pf.get_status_display()})"

        def _stock_label(st):
            unit = "ml" if st.form == "rtf" else "g"
            rem = (
                st.ml_remaining if st.form == "rtf" else st.grams_remaining
            )
            suffix = ""
            try:
                info = st.use_by_info()
                if getattr(info, "label", None):
                    suffix = f" — {info.label}"
            except Exception:
                pass
            return f"{st.product_line} — {rem or 0:g}{unit} left{suffix}"

        formula_source_choices = [("", _("---------"))]
        if prepared:
            formula_source_choices.append(
                (
                    _("Prepared (ready to feed)"),
                    [("prepared:" + str(pf.pk), _prepared_label(pf)) for pf in prepared],
                )
            )
        if rtf:
            formula_source_choices.append(
                (
                    _("Ready-to-feed (pour)"),
                    [("rtf:" + str(st.pk), _stock_label(st)) for st in rtf],
                )
            )
        if powder:
            formula_source_choices.append(
                (
                    _("Formula powder (mix on the spot)"),
                    [("powder:" + str(st.pk), _stock_label(st)) for st in powder],
                )
            )
        self.fields["formula_source"].choices = formula_source_choices

        # Editing: reconstruct picker value from instance FKs
        if self.instance and self.instance.pk:
            if self.instance.prepared_feed_id:
                self.fields["formula_source"].initial = (
                    "prepared:" + str(self.instance.prepared_feed_id)
                )
            elif self.instance.formula_stock_id:
                st = self.instance.formula_stock
                kind = st.form  # "rtf" or "powder"
                self.fields["formula_source"].initial = (
                    kind + ":" + str(self.instance.formula_stock_id)
                )

        # Set initial values from existing instance
        if self.instance and self.instance.pk:
            if self.instance.bottle_brand:
                self.fields["bottle_product"].initial = (
                    f"{self.instance.bottle_brand}||{self.instance.bottle_model or ''}"
                )
            # T6: prefill amount_mixed for unit-linked edits (the picker
            # reconstructs as prepared:<pk>; the field stays editable and
            # re-derives the pool grams on save).
            if self.instance.amount_mixed is not None:
                self.fields["amount_mixed"].initial = (
                    self.instance.amount_mixed
                )

        # Populate nipple_size from inventory
        nipple_sizes = set()
        for si in models.SupplyItem.objects.filter(
            product_line__item_type="bottle_nipples", quantity__gt=0
        ).select_related("product_line"):
            if si.size:
                nipple_sizes.add(si.size)
        for val, label in [
            ("Preemie", _("Preemie")),
            ("0", _("0")),
            ("1", _("1")),
            ("2", _("2")),
            ("2S", _("2S")),
            ("3", _("3")),
            ("4", _("4")),
            ("5", _("5")),
            ("Variable", _("Variable")),
        ]:
            nipple_sizes.add(val)
        self.fields["nipple_size"].choices = [("", _("---------"))] + [
            (s, s) for s in sorted(nipple_sizes)
        ]

    def clean(self):
        cleaned_data = super().clean()


        # Default end to start when omitted (quick-entry convenience;
        # restores b3072001 semantics without hiding the field).
        if not cleaned_data.get("end") and cleaned_data.get("start"):
            cleaned_data["end"] = cleaned_data["start"]
        # Translate bottle_product → bottle_brand + bottle_model
        bottle = cleaned_data.get("bottle_product", "")
        if bottle and "||" in bottle:
            brand, model = bottle.split("||", 1)
            cleaned_data["bottle_brand"] = brand
            cleaned_data["bottle_model"] = model
        else:
            cleaned_data["bottle_brand"] = ""
            cleaned_data["bottle_model"] = ""

        # B7 (2026-08-21): formula_product removed — brand-only feeds
        # are no longer creatable from the form; the source picker
        # derives formula_brand. Editing a legacy brand-only feeding
        # keeps its stored brand unless a source is picked.

        # Formula source picker → prepared_feed / formula_stock FKs +
        # derived brand (spec: selection wins over the standalone brand
        # dropdown; the standalone dropdown stays as the no-selection
        # quick-log fallback).
        src = cleaned_data.pop("formula_source", "") or ""
        if src:
            try:
                kind, pk = src.split(":", 1)
                pk = int(pk)
            except (ValueError, TypeError):
                raise forms.ValidationError(
                    {"formula_source": _("Invalid formula source selection.")}
                )
            if kind == "prepared":
                pf = models.PreparedFeed.objects.filter(pk=pk).first()
                if not pf:
                    raise forms.ValidationError(
                        {
                            "formula_source": _(
                                "Selected prepared bottle no longer exists."
                            )
                        }
                    )
                cleaned_data["prepared_feed"] = pf
                cleaned_data["formula_stock"] = None
                if pf.source_pool:
                    cleaned_data["formula_brand"] = (
                        pf.source_pool.product_line.brand
                    )
            elif kind in ("rtf", "powder"):
                st = models.FormulaStock.objects.filter(pk=pk).first()
                if not st or st.form != kind:
                    raise forms.ValidationError(
                        {
                            "formula_source": _(
                                "Selected formula container no longer exists."
                            )
                        }
                    )
                cleaned_data["formula_stock"] = st
                cleaned_data["prepared_feed"] = None
                cleaned_data["formula_brand"] = st.product_line.brand
            else:
                raise forms.ValidationError(
                    {"formula_source": _("Invalid formula source selection.")}
                )
        else:
            # No explicit source: clear FKs; brand-only legacy fallback
            # (drain-order auto-pick) applies at model save time.
            cleaned_data["prepared_feed"] = None
            cleaned_data["formula_stock"] = None

        # T6 inline prep — "amount mixed" is meaningful ONLY for powder
        # picks. Non-powder or no source: ignore the field entirely
        # (persist None) so non-powder saves are byte-identical to today —
        # EXCEPT edits of feedings already linked to an inline-prep unit
        # (picker reconstructs as prepared:<pk>): keep the submitted value
        # so the pool-grams re-derivation at save has the new mixed
        # amount to work with (None here would read as "never mixed").
        is_powder = bool(
            cleaned_data.get("formula_stock")
            and cleaned_data["formula_stock"].form == "powder"
        )
        was_inline_prep = bool(
            self.instance
            and self.instance.pk
            and self.instance.prepared_feed_id
            and self.instance.amount_mixed is not None
        )
        amount_mixed = cleaned_data.get("amount_mixed")
        if not is_powder and not was_inline_prep:
            cleaned_data["amount_mixed"] = None
        elif is_powder:
            # Compare/default in ml — amount may be logged in oz/tsp/tbsp
            # (same normalization math as Feeding.save()).
            unit = cleaned_data.get("amount_unit") or "ml"
            amount_fed = cleaned_data.get("amount")
            if amount_fed is not None:
                fed_ml = {
                    "oz": amount_fed * 29.5735,
                    "tsp": amount_fed * 5,
                    "tbsp": amount_fed * 15,
                }.get(unit, amount_fed)
                fed_ml = round(fed_ml, 1)
            else:
                fed_ml = None
            # Default = amount fed in ml (direct-pool behavior unless the
            # user says they mixed more).
            if amount_mixed is None:
                cleaned_data["amount_mixed"] = fed_ml
            # Validation: mixed must cover the fed amount.
            elif fed_ml is not None and amount_mixed < fed_ml:
                self.add_error(
                    "amount_mixed",
                    _(
                        "Amount mixed cannot be less than the amount fed."
                    ),
                )
        elif was_inline_prep:
            # Unit-linked edit (picker = prepared:<pk>): the submitted
            # mixed value passes through for save-time re-derivation —
            # but it still must cover the fed amount. Blank submits
            # (field is JS-hidden for prepared picks) keep the
            # persisted value rather than losing it.
            if amount_mixed is None:
                amount_mixed = self.instance.amount_mixed
                cleaned_data["amount_mixed"] = amount_mixed
            unit = cleaned_data.get("amount_unit") or "ml"
            amount_fed = cleaned_data.get("amount")
            if (
                amount_mixed is not None
                and amount_fed is not None
            ):
                fed_ml = {
                    "oz": amount_fed * 29.5735,
                    "tsp": amount_fed * 5,
                    "tbsp": amount_fed * 15,
                }.get(unit, amount_fed)
                if amount_mixed < round(fed_ml, 1):
                    self.add_error(
                        "amount_mixed",
                        _(
                            "Amount mixed cannot be less than the amount fed."
                        ),
                    )

        # Mutual exclusion (model clean() double-checks): at most one of
        # milk item / prepared bottle / formula container.
        if (cleaned_data.get("prepared_feed") or cleaned_data.get("formula_stock")) and cleaned_data.get(
            "feed_inventory"
        ):
            self.add_error(
                "formula_source",
                _(
                    "Select at most one inventory source: a milk "
                    "inventory item, a prepared bottle, or a formula "
                    "container."
                ),
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super(BottleFeedingForm, self).save(commit=False)
        instance.method = "bottle"
        if instance.start and not instance.end:
            instance.end = instance.start
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    class Meta:
        model = models.Feeding
        fields = [
            "child",
            "start",
            "end",
            "type",
            "amount",
            "amount_unit",
            "nipple_size",
            "formula_brand",
            "bottle_brand",
            "bottle_model",
            "previous_feeding",
            "feed_inventory",
            "prepared_feed",
            "formula_stock",
            "amount_mixed",
            "notes",
            "tags",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "type": PillRadioSelect(),
            "amount_unit": PillRadioSelect(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class ChildForm(forms.ModelForm):
    class Meta:
        model = models.Child
        fields = ["first_name", "last_name", "birth_date", "birth_time"]
        if settings.BABY_BUDDY["ALLOW_UPLOADS"]:
            fields.append("picture")
        widgets = {
            "birth_date": DateInput(),
            "birth_time": TimeInput(),
        }


class ChildDeleteForm(forms.ModelForm):
    confirm_name = forms.CharField(max_length=511)

    class Meta:
        model = models.Child
        fields = []

    def clean_confirm_name(self):
        confirm_name = self.cleaned_data["confirm_name"]
        if confirm_name != str(self.instance):
            raise forms.ValidationError(
                _("Name does not match child name."), code="confirm_mismatch"
            )
        return confirm_name

    def save(self, commit=True):
        instance = self.instance
        self.instance.delete()
        return instance


class DiaperChangeForm(CoreModelForm, TaggableModelForm):
    blowout_direction = forms.MultipleChoiceField(
        choices=[
            ("front", _("Front")),
            ("back", _("Back")),
            ("left side", _("Left side")),
            ("right side", _("Right side")),
            ("left leg", _("Left leg")),
            ("right leg", _("Right leg")),
        ],
        required=False,
        widget=PillCheckboxSelect(),
    )
    diaper_product = forms.ChoiceField(
        required=False,
        label=_("Diaper product"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    fieldsets = [
        {"fields": ["child", "time"], "layout": "required"},
        {
            "fields": ["wet", "solid"],
            "layout": "choices",
            "layout_attrs": {"label": "Contents"},
        },
        {
            "fields": ["wet_amount", "solid_amount", "color"],
            "layout": "diaper_change_details",
        },
        {
            "fields": ["blowout", "blowout_direction"],
            "layout": "blowout_details",
        },
        {
            "fields": ["diaper_product", "diaper_size"],
            "layout": "diaper_details",
            "layout_attrs": {"label": "New Clean Diaper Details"},
        },
        {"layout": "advanced", "fields": ["notes", "tags"]},
    ]

    class Meta:
        model = models.DiaperChange
        fields = [
            "child",
            "time",
            "wet",
            "solid",
            "color",
            "amount",
            "wet_amount",
            "solid_amount",
            "blowout",
            "blowout_direction",
            "diaper_size",
            "diaper_brand",
            "diaper_line",
            "notes",
            "tags",
        ]
        widgets = {
            "child": ChildRadioSelect(),
            "color": PillRadioSelect(),
            "wet_amount": PillRadioSelect(),
            "solid_amount": PillRadioSelect(),
            "blowout": PillRadioSelect(),
            "diaper_size": RequiredPillRadioSelect(),
            "time": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Size is required: empty-size changes are invisible to inventory
        # decrement and burn rate (v4 backlog #12). Form-level only — the
        # model stays blank=True and the API serializer stays lenient.
        self.fields["diaper_size"].required = True
        # Convert stored comma-separated string → list for the widget
        if self.instance and self.instance.pk and self.instance.blowout_direction:
            self.initial["blowout_direction"] = [
                d.strip()
                for d in self.instance.blowout_direction.split(",")
                if d.strip()
            ]

        # Populate diaper_product dropdown from ProductLine entries
        choices = [("", _("---------"))]
        for pl in models.ProductLine.objects.filter(item_type="diapers").order_by(
            "brand", "line"
        ):
            choices.append((f"{pl.brand}||{pl.line}", str(pl)))
        self.fields["diaper_product"].choices = choices

        # Set initial value from existing instance
        if self.instance and self.instance.pk and self.instance.diaper_brand:
            initial_val = (
                f"{self.instance.diaper_brand}||{self.instance.diaper_line or ''}"
            )
            self.fields["diaper_product"].initial = initial_val

    def clean(self):
        cleaned_data = super().clean()
        # Translate diaper_product selection → diaper_brand + diaper_line
        product = cleaned_data.get("diaper_product", "")
        if product and "||" in product:
            brand, line = product.split("||", 1)
            cleaned_data["diaper_brand"] = brand
            cleaned_data["diaper_line"] = line
        else:
            cleaned_data["diaper_brand"] = ""
            cleaned_data["diaper_line"] = ""
        return cleaned_data

    def clean_blowout_direction(self):
        """Convert list → comma-separated string for model storage."""
        values = self.cleaned_data.get("blowout_direction", [])
        return ",".join(values) if values else ""


class FeedingForm(CoreModelForm, TaggableModelForm):
    nipple_size = forms.ChoiceField(
        choices=[("", _("---------"))],
        required=False,
        widget=PillRadioSelect(),
    )

    # ProductLine dropdowns — not model fields, translated in clean()
    bottle_product = forms.ChoiceField(
        required=False,
        label=_("Bottle"),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_bottle_product"}),
    )
    # B7 (2026-08-21): free formula_product dropdown removed (see
    # BottleFeedingForm note); formula identity comes from the source
    # picker / prepared feed only.
    # Milk Inventory item this feeding consumes (decrements amount_remaining)
    feed_inventory = forms.ModelChoiceField(
        queryset=models.FeedInventory.objects.none(),
        required=False,
        label=_("Milk inventory item"),
        help_text=_(
            "Optional. Select a Milk Inventory item to decrement its "
            "remaining amount by this feeding's amount."
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    fieldsets = [
        {"fields": ["child", "start", "end", "type", "method"], "layout": "required"},
        {"fields": ["amount", "amount_unit"]},
        {
            "fields": ["breastfeeding_modifier", "sns_amount", "sns_milk_type"],
            "layout": "breastfeeding_modifiers",
        },
        {
            "fields": [
                "bottle_product",
                "nipple_size",
                "feed_inventory",
            ],
            "layout": "bottle_attrs",
        },
        {"fields": ["previous_feeding", "notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Feeding
        fields = [
            "child",
            "start",
            "end",
            "type",
            "method",
            "amount",
            "amount_unit",
            "breastfeeding_modifier",
            "sns_amount",
            "sns_milk_type",
            "nipple_size",
            "formula_brand",
            "bottle_brand",
            "bottle_model",
            "previous_feeding",
            "feed_inventory",
            "notes",
            "tags",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "type": PillRadioSelect(),
            "method": PillRadioSelect(),
            "amount_unit": PillRadioSelect(),
            "breastfeeding_modifier": PillRadioSelect(),
            "sns_milk_type": PillRadioSelect(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate feed_inventory dropdown (same rules as
        # BottleFeedingForm): Milk Inventory items with remaining > 0,
        # plus the currently linked item so edits don't lose it.
        inventory_qs = models.FeedInventory.objects.filter(amount_remaining__gt=0)
        if self.instance and self.instance.feed_inventory_id:
            inventory_qs = inventory_qs | models.FeedInventory.objects.filter(
                pk=self.instance.feed_inventory_id
            )
        self.fields["feed_inventory"].queryset = inventory_qs.order_by(
            "-expressed_at"
        )
        self.fields["feed_inventory"].label_from_instance = lambda obj: (
            f"{obj} — {obj.amount_remaining or 0:g}ml remaining"
        )

        def _feeding_label(f):
            local_start = timezone.localtime(f.start)
            local_end = timezone.localtime(f.end)
            if local_start.strftime("%m/%d") == local_end.strftime("%m/%d"):
                label = f"{local_start.strftime('%m/%d %I:%M %p')} - {local_end.strftime('%I:%M %p')} — {f.get_method_display()}"
            else:
                label = f"{local_start.strftime('%m/%d %I:%M %p')} - {local_end.strftime('%m/%d %I:%M %p')} — {f.get_method_display()}"
            if f.amount:
                label += f" ({f.amount}ml)"
            return label

        # Build previous_feeding choices:
        # - New record: show 15 most recent feedings
        # - Existing record: show feedings within +/-6h of this feeding's start
        pf_choices = [("", _("---------"))]
        if self.instance and self.instance.pk and self.instance.start:
            ref_time = self.instance.start
            window = timezone.timedelta(hours=6)
            feedings = list(
                models.Feeding.objects.filter(
                    end__range=(ref_time - window, ref_time + window)
                ).order_by("-end")
            )
            if self.instance.previous_feeding_id:
                selected_id = self.instance.previous_feeding_id
                if not any(f.id == selected_id for f in feedings):
                    feedings.insert(0, self.instance.previous_feeding)
            for f in feedings:
                if f.pk == self.instance.pk:
                    continue
                pf_choices.append((f.id, _feeding_label(f)))
        else:
            for f in models.Feeding.objects.order_by("-end")[:15]:
                pf_choices.append((f.id, _feeding_label(f)))

        self.fields["previous_feeding"].choices = pf_choices

        # Auto-link previous_feeding if this is a new feeding and the most
        # recent feeding ended within the configured threshold of this one's
        # start time (site setting: FeedingSettings.continuation_threshold_minutes)
        if not (self.instance and self.instance.pk):
            last_feeding = models.Feeding.objects.order_by("-end").first()
            if last_feeding:
                # Check the form's initial start time, or default to now
                start_val = (
                    self.initial.get("start") if hasattr(self, "initial") else None
                )
                if start_val:
                    from datetime import timedelta

                    threshold = models.Feeding.settings.continuation_threshold_minutes
                    if threshold is None:
                        threshold = 30  # default; setting was never saved
                    gap = abs(start_val - last_feeding.end)
                    if gap <= timedelta(minutes=threshold):
                        self.fields["previous_feeding"].initial = last_feeding.id

        # Populate bottle_product dropdown from OWNED equipment (bottles).
        # Equipment is the source of truth for what can actually be used;
        # ProductLine is just the master catalog.
        bottle_choices = [("", _("---------"))]
        seen = set()
        for eq in models.EquipmentItem.objects.filter(
            product_line__item_type="bottles"
        ).select_related("product_line").order_by(
            "product_line__brand", "product_line__line"
        ):
            pl = eq.product_line
            key = (pl.brand, pl.line)
            if key in seen:
                continue
            seen.add(key)
            bottle_choices.append((f"{pl.brand}||{pl.line}", str(pl)))
        self.fields["bottle_product"].choices = bottle_choices

        # Set initial values from existing instance
        if self.instance and self.instance.pk:
            if self.instance.bottle_brand:
                self.fields["bottle_product"].initial = (
                    f"{self.instance.bottle_brand}||{self.instance.bottle_model or ''}"
                )

        # Populate nipple_size from inventory (all bottle_nipples ProductLines)
        nipple_sizes = set()
        for si in models.SupplyItem.objects.filter(
            product_line__item_type="bottle_nipples", quantity__gt=0
        ).select_related("product_line"):
            if si.size:
                nipple_sizes.add(si.size)
        # Also keep hardcoded choices as fallback
        for val, label in [
            ("Preemie", _("Preemie")),
            ("0", _("0")),
            ("1", _("1")),
            ("2", _("2")),
            ("2S", _("2S")),
            ("3", _("3")),
            ("4", _("4")),
            ("5", _("5")),
            ("Variable", _("Variable")),
        ]:
            nipple_sizes.add(val)

        self.fields["nipple_size"].choices = [("", _("---------"))] + [
            (s, s) for s in sorted(nipple_sizes)
        ]

    def clean(self):
        cleaned_data = super().clean()

        # Translate bottle_product → bottle_brand + bottle_model
        bottle = cleaned_data.get("bottle_product", "")
        if bottle and "||" in bottle:
            brand, model = bottle.split("||", 1)
            cleaned_data["bottle_brand"] = brand
            cleaned_data["bottle_model"] = model
        else:
            cleaned_data["bottle_brand"] = ""
            cleaned_data["bottle_model"] = ""

        # B7 (2026-08-21): formula_product removed — brand identity comes
        # from the formula_source picker (or stays as stored history).

        return cleaned_data


class BreastFeedingForm(CoreModelForm, TaggableModelForm):
    """Breast feeding form — shows only breast feeding methods.
    Defaults from last breast feeding entry, independent of bottle/solid."""

    fieldsets = [
        {
            "fields": ["child", "start", "end", "type", "method"],
            "layout": "required",
        },
        {"fields": ["amount", "amount_unit"]},
        {
            "fields": ["breastfeeding_modifier", "sns_amount", "sns_milk_type"],
            "layout": "breastfeeding_modifiers",
        },
        {"fields": ["previous_feeding", "notes", "tags"], "layout": "advanced"},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = [
            ("breast milk", _("Breast milk")),
        ]
        self.fields["method"].choices = [
            ("left breast", _("Left breast")),
            ("right breast", _("Right breast")),
            ("both breasts", _("Both breasts")),
        ]
        # Breast milk is always measured in ml/oz (tsp/tbsp are solid-food units)
        self.fields["amount_unit"].choices = [
            ("ml", _("ml")),
            ("oz", _("oz")),
        ]
        # Build previous_feeding choices (context-aware for existing records)
        if "previous_feeding" in self.fields:
            def _pf_label(f):
                return f"{f.start.strftime('%Y-%m-%d %H:%M')} ({f.get_method_display()})"
            pf_choices = [("", "---------")]
            if self.instance and self.instance.pk and self.instance.start:
                ref_time = self.instance.start
                window = timezone.timedelta(hours=6)
                feedings = list(
                    models.Feeding.objects.filter(
                        end__range=(ref_time - window, ref_time + window)
                    ).order_by("-end")
                )
                if self.instance.previous_feeding_id:
                    selected_id = self.instance.previous_feeding_id
                    if not any(f.id == selected_id for f in feedings):
                        feedings.insert(0, self.instance.previous_feeding)
                for f in feedings:
                    if f.pk == self.instance.pk:
                        continue
                    pf_choices.append((f.id, _pf_label(f)))
            else:
                for f in models.Feeding.objects.order_by("-end")[:10]:
                    pf_choices.append((f.id, _pf_label(f)))
            self.fields["previous_feeding"].choices = pf_choices

    class Meta:
        model = models.Feeding
        fields = [
            "child",
            "start",
            "end",
            "type",
            "method",
            "amount",
            "amount_unit",
            "breastfeeding_modifier",
            "sns_amount",
            "sns_milk_type",
            "previous_feeding",
            "notes",
            "tags",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "type": PillRadioSelect(),
            "method": PillRadioSelect(),
            "amount_unit": PillRadioSelect(),
            "breastfeeding_modifier": PillRadioSelect(),
            "sns_milk_type": PillRadioSelect(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class SolidFeedingForm(CoreModelForm, TaggableModelForm):
    """Solid food feeding form — type auto-set to 'solid food'.
    Shows only 'parent fed' and 'self fed' methods.
    Defaults from last solid food entry."""

    fieldsets = [
        {
            "fields": ["child", "start", "end", "method"],
            "layout": "required",
        },
        {"fields": ["amount", "amount_unit"]},
        {"fields": ["previous_feeding", "notes", "tags"], "layout": "advanced"},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["method"].choices = [
            ("parent fed", _("Parent fed")),
            ("self fed", _("Self fed")),
        ]
        # Solid food is often measured in spoonfuls; tsp/tbsp convert to ml
        self.fields["amount_unit"].choices = [
            ("ml", _("ml")),
            ("oz", _("oz")),
            ("tsp", _("tsp")),
            ("tbsp", _("tbsp")),
        ]
        # Build previous_feeding choices (context-aware for existing records)
        if "previous_feeding" in self.fields:
            def _pf_label(f):
                return f"{f.start.strftime('%Y-%m-%d %H:%M')} ({f.get_method_display()})"
            pf_choices = [("", "---------")]
            if self.instance and self.instance.pk and self.instance.start:
                ref_time = self.instance.start
                window = timezone.timedelta(hours=6)
                feedings = list(
                    models.Feeding.objects.filter(
                        end__range=(ref_time - window, ref_time + window)
                    ).order_by("-end")
                )
                if self.instance.previous_feeding_id:
                    selected_id = self.instance.previous_feeding_id
                    if not any(f.id == selected_id for f in feedings):
                        feedings.insert(0, self.instance.previous_feeding)
                for f in feedings:
                    if f.pk == self.instance.pk:
                        continue
                    pf_choices.append((f.id, _pf_label(f)))
            else:
                for f in models.Feeding.objects.order_by("-end")[:10]:
                    pf_choices.append((f.id, _pf_label(f)))
            self.fields["previous_feeding"].choices = pf_choices

    def save(self, commit=True):
        instance = super(SolidFeedingForm, self).save(commit=False)
        instance.type = "solid food"
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    class Meta:
        model = models.Feeding
        fields = [
            "child",
            "start",
            "end",
            "method",
            "amount",
            "amount_unit",
            "previous_feeding",
            "notes",
            "tags",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "method": PillRadioSelect(),
            "amount_unit": PillRadioSelect(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class HeadCircumferenceForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "head_circumference", "date"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.HeadCircumference
        fields = ["child", "head_circumference", "date", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class HeightForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "height", "date"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Height
        fields = ["child", "height", "date", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class MedicationForm(CoreModelForm, TaggableModelForm):
    next_dose_interval = forms.DecimalField(
        label=_("Time Until Next Dosage"),
        required=False,
        min_value=0,
        initial=0,
        help_text=_("Optional: Hours until next dose can be given"),
    )

    fieldsets = [
        {
            "fields": [
                "child",
                "time",
                "next_dose_interval",
                "name",
                "dosage",
                "dosage_unit",
            ],
            "layout": "required",
        },
        {
            "fields": ["doctor_visit", "prescription", "notes", "tags"],
            "layout": "advanced",
        },
    ]

    class Meta:
        model = models.Medication
        fields = [
            "child",
            "name",
            "dosage",
            "dosage_unit",
            "time",
            "next_dose_interval",
            "doctor_visit",
            "prescription",
            "notes",
            "tags",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "dosage_unit": PillRadioSelect(),
            "time": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert existing timedelta to hours for display
        if self.instance and self.instance.next_dose_interval:
            total_seconds = self.instance.next_dose_interval.total_seconds()
            self.initial["next_dose_interval"] = total_seconds / 3600

    def clean_next_dose_interval(self):
        hours = self.cleaned_data.get("next_dose_interval")
        if hours is not None and hours > 0:
            return timezone.timedelta(hours=float(hours))
        return None


class PrescriptionForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": [
                "child",
                "medication_name",
                "dosage",
                "dosage_unit",
                "frequency",
                "duration",
                "start_date",
            ],
            "layout": "required",
        },
        {
            "fields": [
                "prescribing_doctor",
                "doctor_visit",
                "active",
                "end_date",
                "notes",
                "tags",
            ],
            "layout": "advanced",
        },
    ]

    class Meta:
        model = models.Prescription
        fields = [
            "child",
            "medication_name",
            "dosage",
            "dosage_unit",
            "frequency",
            "duration",
            "prescribing_doctor",
            "doctor_visit",
            "active",
            "start_date",
            "end_date",
            "notes",
            "tags",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "dosage_unit": PillRadioSelect(),
            "start_date": DateInput(),
            "end_date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class PumpingForm(CoreModelForm, TaggableModelForm):
    combine_mode = forms.ChoiceField(
        choices=[("discrete", "discrete"), ("into", "into")],
        initial="discrete",
        required=False,
        widget=forms.HiddenInput(),
    )
    combine_target = forms.ModelChoiceField(
        queryset=models.FeedInventory.objects.none(),
        required=False,
    )

    fieldsets = [
        {"fields": ["child", "start", "end"], "layout": "required"},
        {"fields": ["amount", "amount_unit", "method"]},
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Pumping
        fields = [
            "child",
            "start",
            "end",
            "amount",
            "amount_unit",
            "method",
            "notes",
            "tags",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "amount_unit": PillRadioSelect(),
            "method": PillRadioSelect(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Child is optional (household-scoped pumping)
        self.fields["child"].required = False
        # Combine-at-creation: breast-milk targets only (same-type scope),
        # fresh or thawed — frozen is physically impossible to merge into
        # (fresh liquid into a frozen solid; CDC forbids re-freezing).
        self.fields["combine_target"].queryset = (
            models.FeedInventory.objects.filter(
                type="breast_milk",
                status__in=models.FeedInventory.COMBINE_ELIGIBLE_STATUSES,
            ).order_by("expressed_at")
        )
        # Update form must never silently merge (audit trail only on add)
        if self.instance.pk:
            self.fields["combine_mode"].initial = "discrete"
        else:
            # Wave 3 (2026-08-21): pre-select the site-default pumping
            # method (Settings key, blank = unselected).
            default_method = models.Pumping.settings.default_method
            if default_method:
                self.fields["method"].initial = default_method


class NoteForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.Note
        fields = ["child", "note", "time", "tags"]
        if settings.BABY_BUDDY["ALLOW_UPLOADS"]:
            fields.insert(2, "image")
        widgets = {
            "child": ChildRadioSelect,
            "time": DateTimeInput(),
        }


class SleepForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "start", "end", "nap"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Sleep
        fields = ["child", "start", "end", "nap", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class TagAdminForm(CoreModelForm):
    fieldsets = [
        {
            "fields": ["name", "color"],
            "layout": "required",
        }
    ]

    class Meta:
        model = models.Tag
        fields = ["name", "color"]
        readonly_fields = ["slug"]
        widgets = {
            "color": widgets.TextInput(
                attrs={"type": "color", "class": "form-control-color"}
            )
        }


class TemperatureForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "temperature", "time"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Temperature
        fields = ["child", "temperature", "time", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "time": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class DoctorVisitForm(CoreModelForm):
    fieldsets = [
        {
            "fields": ["child", "date_time", "appointment_type"],
            "layout": "required",
        },
        {
            "fields": ["reason", "symptoms_notes", "doctor_name", "practice"],
            "layout": "advanced",
            "layout_attrs": {"label": "Visit Context"},
        },
        {
            "fields": ["diagnosis", "action_items", "weight_measured"],
            "layout": "advanced",
            "layout_attrs": {"label": "Outcome"},
        },
        {
            "fields": ["notes"],
            "layout": "advanced",
        },
    ]

    class Meta:
        model = models.DoctorVisit
        fields = [
            "child",
            "date_time",
            "appointment_type",
            "doctor_name",
            "practice",
            "reason",
            "symptoms_notes",
            "diagnosis",
            "action_items",
            "weight_measured",
            "notes",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "date_time": DateTimeInput(),
            "appointment_type": PillRadioSelect,
            "doctor_name": forms.Textarea(attrs={"rows": 3}),
            "practice": forms.Textarea(attrs={"rows": 3}),
            "reason": forms.Textarea(attrs={"rows": 3}),
            "symptoms_notes": forms.Textarea(attrs={"rows": 3}),
            "diagnosis": forms.Textarea(attrs={"rows": 3}),
            "action_items": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class TimerForm(CoreModelForm):
    class Meta:
        model = models.Timer
        fields = ["child", "name", "start"]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(TimerForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TimerForm, self).save(commit=False)
        instance.user = self.user
        instance.save()
        return instance


class TummyTimeForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {"fields": ["child", "start", "end"], "layout": "required"},
        {"fields": ["milestone"]},
        {"fields": ["tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.TummyTime
        fields = ["child", "start", "end", "milestone", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
        }


class WeightForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "weight", "date"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Weight
        fields = ["child", "weight", "date", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class SupplyItemForm(CoreModelForm):
    """
    Add/restock inventory. User picks product line (or creates new),
    picks size, enters pack info. On save, quantity is ADDED to the
    matching pool (or a new pool is created).
    """

    # Restock fields — not model fields, processed in save()
    pack_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("e.g. box, bag, loose")}),
    )
    items_per_pack = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={"placeholder": _("e.g. 140")}),
    )
    number_of_packs = forms.IntegerField(
        required=False,
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"placeholder": _("e.g. 2")}),
    )

    fieldsets = [
        {"fields": ["child", "product_line", "size"], "layout": "required"},
        {
            "fields": [
                "pack_type",
                "items_per_pack",
                "number_of_packs",
                "acquisition_date",
                "usage_eligible",
                "is_reserve",
                "drain_priority",
            ]
        },
        {"fields": ["notes"], "layout": "advanced"},
    ]

    class Meta:
        model = models.SupplyItem
        fields = [
            "child",
            "product_line",
            "size",
            "acquisition_date",
            "usage_eligible",
            "is_reserve",
            "drain_priority",
            "notes",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "product_line": forms.Select(),
            "size": forms.TextInput(attrs={"placeholder": _("e.g. 1, 2, NB, 4oz...")}),
            "acquisition_date": DateTimeInput(),
            "usage_eligible": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Group product lines by type — consumables only (diapers, wipes)
        from collections import OrderedDict

        choices = [("", _("---------"))]
        # Only show consumable types in the dropdown
        consumable_types = [t for t in dict(models.ProductLine.ITEM_TYPES)
                           if t in ("diapers", "wipes")]
        pl_type_labels = dict(models.ProductLine.ITEM_TYPES)
        for item_type in consumable_types:
            type_label = pl_type_labels[item_type]
            pls = models.ProductLine.objects.filter(item_type=item_type).order_by(
                "brand", "line"
            )
            if pls.exists():
                group = [(pl.id, str(pl)) for pl in pls]
                choices.append((type_label, group))
        self.fields["product_line"].choices = choices

        # Household stock: child is optional on every pool
        self.fields["child"].required = False
        self.fields["child"].empty_label = _("— Household —")
        if not self.instance or not self.instance.pk:
            self.fields["child"].initial = None

        # If editing existing item, fill restock fields with current state
        if self.instance and self.instance.pk:
            self.fields["number_of_packs"].initial = 0
            self.fields["number_of_packs"].min_value = 0
            self.fields["number_of_packs"].help_text = _(
                "Enter quantity to ADD to existing pool (%d current)."
                % self.instance.quantity
            )

    def save(self, commit=True):
        instance = super().save(commit=False)

        packs = self.cleaned_data.get("number_of_packs") or 0
        items_per = self.cleaned_data.get("items_per_pack") or 0
        pack_type = self.cleaned_data.get("pack_type", "")

        # Determine items per pack and pack count
        if items_per and items_per > 0 and packs and packs > 0:
            # Multi-pack: create N separate pools, each with items_per items
            if commit:
                instance.quantity = items_per
                instance.initial_quantity = items_per
                instance.save()
                self.save_m2m()
                models.InventoryTransaction.objects.create(
                    supply_item=instance,
                    delta=items_per,
                    transaction_type="restock",
                    quantity_after=instance.quantity,
                    note="Restock via supply form: %d pack(s) x %d each"
                    % (packs, items_per),
                )

                # Create remaining packs as separate pools
                for i in range(1, packs):
                    new_pool = models.SupplyItem.objects.create(
                        child=instance.child,
                        product_line=instance.product_line,
                        size=instance.size,
                        quantity=items_per,
                        initial_quantity=items_per,
                        acquisition_date=instance.acquisition_date,
                        usage_eligible=instance.usage_eligible,
                        is_reserve=instance.is_reserve,
                        drain_priority=instance.drain_priority,
                        notes=instance.notes,
                    )
                    models.InventoryTransaction.objects.create(
                        supply_item=new_pool,
                        delta=items_per,
                        transaction_type="restock",
                        quantity_after=new_pool.quantity,
                        note="Restock via supply form: pack %d of %d"
                        % (i + 1, packs),
                    )
            return instance

        elif packs and packs > 0 and not items_per:
            # No items_per_pack — treat as individual loose items, single pool
            before = instance.quantity
            instance.quantity += packs
            instance.initial_quantity += packs
            if commit:
                models.InventoryTransaction.objects.create(
                    supply_item=instance,
                    delta=packs,
                    transaction_type="restock",
                    quantity_after=instance.quantity,
                    note="Restock via supply form: %d loose item(s)" % packs,
                )
        # else: no packs specified, just save as-is

        if commit:
            instance.save()
            self.save_m2m()
        return instance


class SupplyItemUpdateForm(CoreModelForm):
    """
    Edit an existing pool's permanent/original metadata: product, size,
    original count, acquisition/usage-eligible dates, reserve flag,
    drain priority, notes.

    Deliberately does NOT include live quantity (use Physical count /
    Adjust for corrections) or pack fields (use Add to bring in new
    stock — each restock becomes its own pool row).
    """

    fieldsets = [
        {
            "fields": ["child", "product_line", "size", "initial_quantity"],
            "layout": "required",
        },
        {
            "fields": [
                "acquisition_date",
                "usage_eligible",
                "is_reserve",
                "drain_priority",
            ]
        },
        {"fields": ["notes"], "layout": "advanced"},
    ]

    class Meta:
        model = models.SupplyItem
        fields = [
            "child",
            "product_line",
            "size",
            "initial_quantity",
            "acquisition_date",
            "usage_eligible",
            "is_reserve",
            "drain_priority",
            "notes",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "product_line": forms.Select(),
            "size": forms.TextInput(
                attrs={"placeholder": _("e.g. 1, 2, NB, 4oz...")}
            ),
            "acquisition_date": DateTimeInput(),
            "usage_eligible": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Group product lines by type — same consumable grouping as add form
        choices = [("", _("---------"))]
        pl_type_labels = dict(models.ProductLine.ITEM_TYPES)
        for item_type in ("diapers", "wipes"):
            type_label = pl_type_labels[item_type]
            pls = models.ProductLine.objects.filter(item_type=item_type).order_by(
                "brand", "line"
            )
            if pls.exists():
                group = [(pl.id, str(pl)) for pl in pls]
                choices.append((type_label, group))
        self.fields["product_line"].choices = choices
        self.fields["child"].required = False
        self.fields["child"].empty_label = _("— Household —")
        if self.instance and self.instance.pk:
            self.fields["initial_quantity"].help_text = _(
                "Original count when acquired (%d currently on hand). "
                "Lowering it below current on-hand also corrects on-hand "
                "down by the shortfall."
                % self.instance.quantity
            )
            self._original = {
                "is_reserve": self.instance.is_reserve,
                "usage_eligible": self.instance.usage_eligible,
                "initial_quantity": self.instance.initial_quantity,
            }
        else:
            self._original = {}

    def clean_initial_quantity(self):
        # Lowering the original count below current on-hand means the
        # excess was never physically there (wrong initial entry).
        # Correct on-hand down by the same shortfall in save(), audited.
        value = self.cleaned_data.get("initial_quantity")
        self._overcount_fix = 0
        if self.instance and self.instance.pk:
            if value < self.instance.initial_quantity and self.instance.quantity > value:
                self._overcount_fix = self.instance.quantity - value
        return value

    def save(self, commit=True):
        fix = getattr(self, "_overcount_fix", 0)
        if fix and self.instance and self.instance.pk:
            self.instance.quantity = max(0, self.instance.quantity - fix)
        instance = super().save(commit=commit)
        if commit and self._original:
            changes = []
            if fix:
                changes.append(
                    "original count over-stated; on-hand corrected by -%d" % fix
                )
            if self._original["is_reserve"] != instance.is_reserve:
                changes.append(
                    "reserve %s -> %s"
                    % (self._original["is_reserve"], instance.is_reserve)
                )
            if self._original["usage_eligible"] != instance.usage_eligible:
                changes.append(
                    "usage_eligible %s -> %s"
                    % (self._original["usage_eligible"], instance.usage_eligible)
                )
            if self._original["initial_quantity"] != instance.initial_quantity:
                changes.append(
                    "initial_quantity %s -> %s"
                    % (self._original["initial_quantity"], instance.initial_quantity)
                )
            if changes:
                models.InventoryTransaction.objects.create(
                    supply_item=instance,
                    delta=-fix,
                    transaction_type="adjustment",
                    quantity_after=instance.quantity,
                    note="Pool metadata edit: " + "; ".join(changes),
                )
        return instance


class ProductLineForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {"fields": ["item_type", "brand", "line"], "layout": "required"},
        {
            "fields": ["scoop_grams", "water_per_scoop_ml"],
            "layout": "advanced",
            "layout_attrs": {
                "label": _("Formula Mixing Ratio (powder pools only)")
            },
        },
    ]

    class Meta:
        model = models.ProductLine
        fields = ["item_type", "brand", "line", "scoop_grams", "water_per_scoop_ml"]
        widgets = {
            "item_type": PillRadioSelect(),
            "brand": forms.TextInput(
                attrs={"placeholder": _("e.g. Pampers, Dr. Brown's...")}
            ),
            "line": forms.TextInput(
                attrs={"placeholder": _("e.g. Swaddlers, Wide-Neck... (optional)")}
            ),
        }

    def clean(self):
        cleaned = super().clean()
        scoop = cleaned.get("scoop_grams")
        water = cleaned.get("water_per_scoop_ml")
        if (scoop is None) != (water is None):
            raise forms.ValidationError(
                {
                    "scoop_grams": _(
                        "Set both scoop grams and water per scoop, or leave both clear."
                    )
                }
            )
        if scoop is not None and scoop <= 0:
            self.add_error("scoop_grams", _("Must be greater than zero."))
        if water is not None and water <= 0:
            self.add_error("water_per_scoop_ml", _("Must be greater than zero."))
        return cleaned


class SpitUpForm(CoreModelForm):
    fieldsets = [
        {"fields": ["child", "time", "amount", "appearance"], "layout": "required"},
        {
            "fields": ["related_feeding"],
            "layout": "advanced",
            "layout_attrs": {"label": "Link to Feeding"},
        },
        {"fields": ["notes"], "layout": "advanced"},
    ]

    class Meta:
        model = models.SpitUp
        fields = ["child", "time", "amount", "appearance", "related_feeding", "notes"]
        widgets = {
            "child": ChildRadioSelect,
            "time": DateTimeInput(),
            "amount": PillRadioSelect(),
            "related_feeding": forms.Select(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        def _feeding_label(f):
            local_start = timezone.localtime(f.start)
            local_end = timezone.localtime(f.end)
            if local_start.strftime("%m/%d") == local_end.strftime("%m/%d"):
                label = f"{local_start.strftime('%m/%d %I:%M %p')} - {local_end.strftime('%I:%M %p')} — {f.get_method_display()}"
            else:
                label = f"{local_start.strftime('%m/%d %I:%M %p')} - {local_end.strftime('%m/%d %I:%M %p')} — {f.get_method_display()}"
            if f.amount:
                label += f" ({f.amount}ml)"
            return label

        # Build related_feeding choices (context-aware for existing records)
        choices = [("", _("---------"))]
        if self.instance and self.instance.pk and self.instance.time:
            ref_time = self.instance.time
            window = timezone.timedelta(hours=6)
            feedings = list(
                models.Feeding.objects.filter(
                    end__range=(ref_time - window, ref_time + window)
                ).order_by("-end")
            )
            if self.instance.related_feeding_id:
                selected_id = self.instance.related_feeding_id
                if not any(f.id == selected_id for f in feedings):
                    feedings.insert(0, self.instance.related_feeding)
            for f in feedings:
                choices.append((f.id, _feeding_label(f)))
        else:
            for f in models.Feeding.objects.order_by("-end")[:20]:
                choices.append((f.id, _feeding_label(f)))
            latest = models.Feeding.objects.order_by("-end").first()
            if latest:
                self.fields["related_feeding"].initial = latest.id

        self.fields["related_feeding"].choices = choices

        # Auto-select most recent feeding as default
        if not (self.instance and self.instance.pk):
            latest = models.Feeding.objects.order_by("-end").first()
            if latest:
                self.fields["related_feeding"].initial = latest.id


class EquipmentItemForm(CoreModelForm):
    fieldsets = [
        {"fields": ["product_line", "child", "size", "quantity"], "layout": "required"},
        {
            "fields": ["acquired_date", "source"],
            "layout": "advanced",
            "layout_attrs": {"label": "Acquisition Details"},
        },
        {
            "fields": ["disposal_status", "disposal_date"],
            "layout": "advanced",
            "layout_attrs": {"label": "Disposal (if applicable)"},
        },
        {"fields": ["notes"], "layout": "advanced"},
    ]

    class Meta:
        model = models.EquipmentItem
        fields = [
            "product_line",
            "child",
            "size",
            "quantity",
            "acquired_date",
            "source",
            "disposal_status",
            "disposal_date",
            "notes",
        ]
        widgets = {
            "child": ChildRadioSelect(),
            "quantity": forms.NumberInput(attrs={"min": 1}),
            "acquired_date": forms.DateInput(attrs={"type": "date"}),
            "disposal_date": forms.DateInput(attrs={"type": "date"}),
            "disposal_status": forms.Select(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default disposal_status to owned for new entries
        if not (self.instance and self.instance.pk):
            self.fields["disposal_status"].initial = "owned"
        # Populate product_line dropdown scoped to durable item types only
        durable_types = ["bottles", "bottle_nipples", "other"]
        from core.models import ProductLine

        choices = [("", _("---------"))]
        for pl in ProductLine.objects.filter(item_type__in=durable_types).order_by(
            "item_type", "brand", "line"
        ):
            label = f"{pl.get_item_type_display()}: {pl.brand}"
            if pl.line:
                label += f" {pl.line}"
            choices.append((pl.id, label))
        self.fields["product_line"].choices = choices


class FeedInventoryForm(CoreModelForm, TaggableModelForm):
    # Optional child — feed belongs to the household pool, not one child.
    child = forms.ModelChoiceField(
        queryset=models.Child.objects.all(),
        required=False,
        widget=ChildRadioSelect(),
        label=_("Child"),
        help_text=_("Optional. Leave blank for household milk pool."),
    )

    fieldsets = [
        {
            "fields": [
                "child",
                "type",
                "pumping_session",
                "amount",
                "amount_unit",
                "storage_location",
                "status",
                "expressed_at",
            ],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.FeedInventory
        fields = [
            "child",
            "type",
            "pumping_session",
            "amount",
            "amount_unit",
            "storage_location",
            "status",
            "expressed_at",
            "notes",
            "tags",
        ]
        widgets = {
            "type": PillRadioSelect(),
            "pumping_session": forms.Select(),
            "amount_unit": PillRadioSelect(),
            "storage_location": PillRadioSelect(),
            "status": PillRadioSelect(),
            "expressed_at": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def _pumping_label(p):
            local_start = timezone.localtime(p.start)
            local_end = timezone.localtime(p.end)
            if local_start.strftime("%m/%d") == local_end.strftime("%m/%d"):
                label = (
                    f"{local_start.strftime('%m/%d %I:%M %p')} - "
                    f"{local_end.strftime('%I:%M %p')}"
                )
            else:
                label = (
                    f"{local_start.strftime('%m/%d %I:%M %p')} - "
                    f"{local_end.strftime('%m/%d %I:%M %p')}"
                )
            if p.amount:
                label += f" ({p.amount:g}{p.amount_unit or 'ml'})"
            if p.method:
                label += f" — {p.get_method_display()}"
            if p.child:
                label += f" — {p.child}"
            return label

        # Build pumping_session choices (context-aware for existing records)
        pump_choices = [("", _("---------"))]
        if self.instance and self.instance.pk and self.instance.expressed_at:
            ref_time = self.instance.expressed_at
            window = timezone.timedelta(hours=12)
            sessions = list(
                models.Pumping.objects.filter(
                    end__range=(ref_time - window, ref_time + window)
                ).order_by("-end")
            )
            if self.instance.pumping_session_id:
                selected_id = self.instance.pumping_session_id
                if not any(p.pk == selected_id for p in sessions):
                    sessions.insert(0, self.instance.pumping_session)
            for p in sessions:
                # The linked session is included deliberately, even when it
                # is outside the ±12h window: it is the CURRENT value of the
                # FK. Skipping it renders the dropdown empty when no other
                # session is nearby, and saving then silently clears the FK.
                pump_choices.append((p.pk, _pumping_label(p)))
        else:
            for p in models.Pumping.objects.order_by("-end")[:15]:
                pump_choices.append((p.pk, _pumping_label(p)))

        self.fields["pumping_session"].choices = pump_choices

    def clean(self):
        cleaned = super().clean()
        location = cleaned.get("storage_location")
        status = cleaned.get("status")
        if location and status:
            derived = models.FeedInventory.derive_status(status, location)
            if derived != status:
                # Status must reflect the physical state (DECIDED
                # 2026-08-17). Report instead of silently overriding so
                # the user sees what the location implies.
                self.add_error(
                    "status",
                    _("Status should be “%(derived)s” for location “%(location)s”.")
                    % {
                        "derived": derived,
                        "location": location,
                    },
                )
        return cleaned


class ConsumeFeedInventoryForm(forms.Form):
    """Form to consume (decrement) a partial amount from a FeedInventory entry."""

    amount = forms.FloatField(
        min_value=0.01,
        label=_("Amount to consume (ml)"),
        help_text=_("Enter the amount in ml to remove from this inventory entry."),
    )

    def __init__(self, *args, **kwargs):
        self.inventory = kwargs.pop("inventory", None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if self.inventory and self.inventory.amount_remaining is not None:
            if amount > self.inventory.amount_remaining:
                raise forms.ValidationError(
                    _("Cannot consume %(requested).1f ml — only %(remaining).1f ml remaining.")
                    % {
                        "requested": amount,
                        "remaining": self.inventory.amount_remaining,
                    }
                )
        return amount
def _unit_label(obj):
    """Card-style label for combine form rows."""
    when = (
        obj.expressed_at.strftime("%m/%d %H:%M") if obj.expressed_at else "—"
    )
    label = "{lbl} · {amount:g} {unit} · {status} · {location} · {when}".format(
        lbl=obj.label or ("#%d" % obj.pk),
        amount=obj.amount_remaining or obj.amount or 0,
        unit=obj.amount_unit,
        status=obj.get_status_display(),
        location=obj.get_storage_location_display(),
        when=when,
    )
    return label


class CombineFeedInventoryForm(forms.Form):
    """Combine (merge) inventory entries (combine v2)."""

    def __init__(self, *args, **kwargs):
        self.inventory = kwargs.pop("inventory", None)
        super().__init__(*args, **kwargs)
        if self.inventory:
            # v2: household-level — child dropped from the queryset; type
            # stays (different products/clocks); fresh AND thawed are
            # combinable (matrix decides the result), frozen is blocked.
            pool = models.FeedInventory.objects.filter(
                type=self.inventory.type,
                status__in=models.FeedInventory.COMBINE_ELIGIBLE_STATUSES,
            ).order_by("expressed_at")
            others = pool.exclude(pk=self.inventory.pk)
            self.fields["entries"] = forms.ModelMultipleChoiceField(
                queryset=others,
                widget=forms.CheckboxSelectMultiple,
                label=_("Entries to combine"),
                help_text=_(
                    "Fresh or thawed entries of the same type. Frozen "
                    "units cannot be merged."
                ),
            )
            self.fields["entries"].label_from_instance = _unit_label
            # Which identity survives the merge. Clocks ALWAYS min-merge
            # (oldest wins) regardless of this choice; this only picks
            # the surviving label/ID/row. Default = oldest unit.
            survivor_pool = list(pool)
            oldest = survivor_pool[0] if survivor_pool else None
            self.fields["survivor"] = forms.ModelChoiceField(
                queryset=pool,
                widget=forms.RadioSelect,
                initial=oldest,
                label=_("Unit that survives (keeps its label/ID)"),
                help_text=_(
                    "Storage clocks always min-merge to the oldest "
                    "regardless of this choice."
                ),
            )
            self.fields["survivor"].label_from_instance = _unit_label

    def clean(self):
        cleaned = super().clean()
        entries = cleaned.get("entries")
        if self.inventory and entries:
            statuses = [self.inventory.status] + [e.status for e in entries]
            if any(s == "frozen" for s in statuses):
                raise forms.ValidationError(
                    _("Frozen units cannot be combined.")
                )
            if any(
                s not in models.FeedInventory.COMBINE_ELIGIBLE_STATUSES
                for s in statuses
            ):
                raise forms.ValidationError(
                    _("Only fresh or thawed units can be combined.")
                )
        return cleaned


class CombineIntoFeedInventoryForm(forms.Form):
    """Reverse combine: merge THIS unit into a chosen target (v3)."""

    def __init__(self, *args, **kwargs):
        self.inventory = kwargs.pop("inventory", None)
        super().__init__(*args, **kwargs)
        if self.inventory:
            pool = models.FeedInventory.objects.filter(
                type=self.inventory.type,
                status__in=models.FeedInventory.COMBINE_ELIGIBLE_STATUSES,
            ).exclude(pk=self.inventory.pk).order_by("expressed_at")
            self.fields["target"] = forms.ModelChoiceField(
                queryset=pool,
                label=_(("Combine into")),
                help_text=_(
                    "This unit is absorbed into the chosen target. The "
                    "target keeps its label; clocks min-merge per the "
                    "combine matrix."
                ),
            )
            self.fields["target"].label_from_instance = _unit_label

    def clean(self):
        cleaned = super().clean()
        if self.inventory and self.inventory.status not in (
            models.FeedInventory.COMBINE_ELIGIBLE_STATUSES
        ):
            raise forms.ValidationError(
                _("Only fresh or thawed units can be combined.")
            )
        return cleaned


class SplitFeedInventoryForm(forms.Form):
    """Split off a portion of this entry into a new entry."""

    amount = forms.FloatField(
        min_value=0.01,
        label=_(("Amount to split off (ml)")),
        help_text=_("Create a new entry with this amount; the remainder stays here."),
    )
    storage_location = forms.ChoiceField(
        choices=models.FeedInventory._meta.get_field("storage_location").choices,
        label=_(("Storage location")),
        help_text=_("Storage location for the NEW entry."),
    )

    status = forms.ChoiceField(
        choices=models.FeedInventory._meta.get_field("status").choices,
        label=_("Status"),
        help_text=_(
            "Auto-derived from the source entry and the chosen location "
            "(status reflects the physical state: fresh milk going to a "
            "freezer is frozen; previously-frozen milk anywhere else is "
            "thawing). Adjust only if the derivation is wrong."
        ),
    )

    @staticmethod
    def derive_status(source_status, destination):
        """Derive the split-off entry's status.

        Delegates to FeedInventory.derive_status (physical-state
        convention, DECIDED 2026-08-17): status reflects the unit's
        current physical state — fresh milk moved to a freezer is
        "frozen"; previously-frozen milk anywhere but a freezer is
        "thawed" and can never go back to "fresh".
        """
        return models.FeedInventory.derive_status(source_status, destination)

    def __init__(self, *args, **kwargs):
        self.inventory = kwargs.pop("inventory", None)
        super().__init__(*args, **kwargs)
        if self.inventory:
            self.fields["storage_location"].initial = self.inventory.storage_location
            self.fields["status"].initial = self.derive_status(
                self.inventory.status, self.inventory.storage_location
            )
            self.fields["amount"].help_text = _(
                "Create a new entry with this amount; %(rem).1f ml currently remains here."
            ) % {"rem": self.inventory.amount_remaining or 0}

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if self.inventory and self.inventory.amount_remaining is not None:
            if amount >= self.inventory.amount_remaining:
                raise forms.ValidationError(
                    _(
                        "Split amount must be less than the %(rem).1f ml remaining "
                        "(use Combine for full merges)."
                    )
                    % {"rem": self.inventory.amount_remaining}
                )
        return amount


class SupplyItemAdjustForm(forms.Form):
    """Form to manually adjust a SupplyItem pool's quantity."""
    physical_count = forms.IntegerField(
        label=_("Physical count"),
        help_text=_("Enter the actual number of items on hand."),
    )
    count_time = forms.DateTimeField(
        label=_("Count time"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text=_("When this count was taken. Defaults to now."),
    )
    reason = forms.CharField(
        required=False,
        max_length=255,
        label=_("Reason"),
        widget=forms.TextInput(attrs={"placeholder": _("e.g. 'Counted in drawer'")}),
    )

    def __init__(self, *args, **kwargs):
        self.supply_item = kwargs.pop("supply_item", None)
        super().__init__(*args, **kwargs)
        if not self.initial.get("count_time"):
            from django.utils import timezone
            self.initial["count_time"] = timezone.now().strftime("%Y-%m-%dT%H:%M")
        if self.supply_item and not self.initial.get("physical_count"):
            self.initial["physical_count"] = self.supply_item.quantity


class PhysicalCountForm(forms.Form):
    """Header form for a physical count session."""
    count_time = forms.DateTimeField(
        label=_("Count time"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text=_("When this physical count was taken."),
    )
    notes = forms.CharField(
        required=False,
        max_length=500,
        label=_("Notes"),
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Preview only (don't update pools)"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        if not self.initial.get("count_time"):
            self.initial["count_time"] = timezone.now().strftime("%Y-%m-%dT%H:%M")


class PhysicalCountLineForm(forms.Form):
    """One line item in a physical count — product + size + count."""

    SIZE_CHOICES = [
        ("", "---------"),
        ("P", "P (Preemie)"),
        ("NB", "NB (Newborn)"),
        ("1", "1"),
        ("2", "2"),
        ("3", "3"),
        ("4", "4"),
        ("5", "5"),
        ("6", "6"),
    ]

    product = forms.ChoiceField(
        required=False,
        label=_("Product"),
        widget=forms.Select(attrs={"class": "form-select product-select"}),
    )
    size = forms.ChoiceField(
        required=False,
        choices=SIZE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    physical_count = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "---------")]
        for pl in models.ProductLine.objects.filter(
            item_type__in=["diapers", "wipes"]
        ).order_by("item_type", "brand", "line"):
            choices.append((f"{pl.brand}||{pl.line}", str(pl)))
        self.fields["product"].choices = choices


class FormulaStockForm(CoreModelForm):
    """
    Add/restock formula stock. User picks product line (formula type
    only), form (powder/RTF), and container size. T2 builds the
    open-container flow; T4 the prep flows.
    """

    fieldsets = [
        {
            "fields": ["product_line", "form", "container_size", "quantity"],
            "layout": "required",
        },
        {
            "fields": [
                "expiry_date",
                "acquisition_date",
                "usage_eligible",
                "drain_priority",
                "is_reserve",
            ]
        },
        {
            "fields": ["opened_at", "grams_remaining", "ml_remaining"],
            "layout": "advanced",
            "layout_attrs": {"label": "Already opened?"},
        },
        {"fields": ["notes"], "layout": "advanced"},
    ]

    class Meta:
        model = models.FormulaStock
        fields = [
            "product_line",
            "form",
            "container_size",
            "quantity",
            "expiry_date",
            "acquisition_date",
            "usage_eligible",
            "drain_priority",
            "is_reserve",
            "opened_at",
            "grams_remaining",
            "ml_remaining",
            "notes",
        ]
        widgets = {
            "product_line": forms.Select(),
            "form": PillRadioSelect(),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "acquisition_date": DateTimeInput(),
            "usage_eligible": DateTimeInput(),
            "opened_at": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product_line"].queryset = (
            models.ProductLine.objects.filter(item_type="formula").order_by(
                "brand", "line"
            )
        )

    def clean(self):
        cleaned = super().clean()
        form_val = cleaned.get("form")
        # B4 (2026-08-21): one product line may host both a powder pool
        # and an RTF pool — ratio fields are powder-only facts on the
        # product line and are ignored for ready-to-feed pools. The old
        # cross-check that rejected RTF on a ratio-bearing line is gone.
        opened = cleaned.get("opened_at")
        initial_grams = cleaned.get("grams_remaining")
        initial_ml = cleaned.get("ml_remaining")
        if opened is not None:
            # An opened row is exactly ONE container — set, don't ask.
            cleaned["quantity"] = 1
            if form_val == "powder":
                cleaned["ml_remaining"] = None
                if initial_grams is None:
                    self.add_error(
                        "grams_remaining",
                        _("Enter the grams currently in the opened can."),
                    )
            if form_val == "rtf":
                cleaned["grams_remaining"] = None
                if initial_ml is None:
                    self.add_error(
                        "ml_remaining",
                        _("Enter the ml currently in the opened container."),
                    )
        return cleaned


class OpenFormulaStockForm(forms.Form):
    """Confirm-open form: when + optional note."""

    opened_at = forms.DateTimeField(
        label=_("Opened at"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text=_("Clock start for the opened container."),
    )
    note = forms.CharField(
        label=_("Note"),
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={"placeholder": _("Optional note (recorded in the ledger)")}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone

        self.initial.setdefault("opened_at", timezone.now())

    def clean_opened_at(self):
        from django.utils import timezone

        value = self.cleaned_data["opened_at"]
        if timezone.is_naive(value):
            value = timezone.make_aware(value)
        if value > timezone.now() + timezone.timedelta(minutes=5):
            raise forms.ValidationError(
                _("Date/time cannot be more than 5 minutes in the future.")
            )
        if value.year < 2020:
            raise forms.ValidationError(
                _("Date/time is implausibly old.")
            )
        return value


class MarkWarmedForm(forms.Form):
    """B2 (2026-08-21): confirm-warmed form for milk inventory units."""

    warmed_at = forms.DateTimeField(
        label=_("Warmed at"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text=_(
            "When the unit was warmed. One-way: starts the 2h clock "
            "and blocks returning this unit to cold storage."
        ),
    )
    note = forms.CharField(
        label=_("Note"),
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={"placeholder": _("Optional note (recorded in the ledger)")}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial.setdefault("warmed_at", timezone.now())

    def clean_warmed_at(self):
        value = self.cleaned_data["warmed_at"]
        if timezone.is_naive(value):
            value = timezone.make_aware(value)
        if value > timezone.now() + timezone.timedelta(minutes=5):
            raise forms.ValidationError(
                _("Date/time cannot be more than 5 minutes in the future.")
            )
        if value.year < 2020:
            raise forms.ValidationError(
                _("Date/time is implausibly old.")
            )
        return value


class FormulaStockAdjustForm(forms.Form):
    """Manual adjust of an opened container's remaining amount.

    Physical-count semantics (SupplyItem convention): you type the
    actual grams/ml left in the container; the delta is computed and
    recorded in the ledger with a reason.
    """

    physical_amount = forms.FloatField(
        label=_("Actual amount remaining"),
        min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.1"}),
        help_text=_("Grams (powder) or ml (RTF) actually left."),
    )
    reason = forms.ChoiceField(
        label=_("Reason"),
        choices=[
            ("physical_count", _("Physical count / reconciliation")),
            ("spillage", _("Spillage / waste")),
            ("evaporation", _("Evaporation / drift")),
            ("other", _("Other (note below)")),
        ],
        initial="physical_count",
    )
    note = forms.CharField(
        label=_("Note"),
        required=False,
        max_length=255,
    )
    count_time = forms.DateTimeField(
        label=_("Count time"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    def __init__(self, *args, **kwargs):
        self.stock = kwargs.pop("stock", None)
        super().__init__(*args, **kwargs)
        from django.utils import timezone

        self.initial.setdefault("count_time", timezone.now())
        if self.stock is not None and self.stock.is_open:
            current = (
                self.stock.grams_remaining
                if self.stock.form == "powder"
                else self.stock.ml_remaining
            )
            self.initial.setdefault("physical_amount", current or 0)

    def clean(self):
        cleaned = super().clean()
        if self.stock is not None and not self.stock.is_open:
            raise forms.ValidationError(
                _("Manual adjust applies to opened containers only.")
            )
        return cleaned


class PreparedFeedForm(CoreModelForm):
    """
    Standalone prep logging (DECISION #2 path A). Pool decrement at prep
    happens in PreparedFeed.save() (T4 bite 3). source_inventory is
    reserved/unwired (DECISION #5) and excluded from the form.

    Prefill rules (user decision 2026-08-20): prepared_at = now() on
    create; fridge_entered_at = now() iff blank AND storage context is
    fridge — on PreparedFeed the fridge timestamp IS the storage signal
    (no separate storage field), so the prefill fires iff the user
    populates it while opening the form... in practice: the add form
    leaves it blank (bottle not yet in fridge); the update form
    prefills now() iff blank AND the unit's clock is currently
    fridge-anchored.
    """

    fieldsets = [
        {
            "fields": ["prepared_from", "source_pool", "amount", "prepared_at"],
            "layout": "required",
        },
        {
            "fields": ["fridge_entered_at", "grams_used", "notes"],
            "layout": "advanced",
        },
    ]

    class Meta:
        model = models.PreparedFeed
        fields = [
            "prepared_from",
            "source_pool",
            "amount",
            "prepared_at",
            "fridge_entered_at",
            "grams_used",
            "notes",
        ]
        widgets = {
            "prepared_from": PillRadioSelect(),
            "source_pool": forms.Select(),
            "prepared_at": DateTimeInput(),
            "fridge_entered_at": DateTimeInput(),
            "grams_used": forms.NumberInput(
                attrs={
                    "placeholder": _(
                        "Auto-computed from the product's mixing ratio"
                    )
                }
            ),
        }
        labels = {
            "grams_used": _("Powder grams used"),
        }
        help_texts = {
            "grams_used": _(
                "Auto-calculated on save from the mixing ratio — "
                "fill in only to override."
            ),
            "fridge_entered_at": _(
                "Leave blank for a room-temperature bottle (2h clock "
                "from save). Fill in when the bottle goes into the "
                "fridge."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_pool"].queryset = (
            models.FormulaStock.objects.filter(opened_at__isnull=False)
            .exclude(is_reserve=True)
        )
        # Prefill (2026-08-20 rules): create → prepared_at = now().
        # Update → fridge_entered_at = now() iff blank + fridge-anchored
        # (clock reason "fridge" = has fridge_entered_at... which is
        # blank here, so the anchor condition is: user moved the bottle
        # to fridge WITHOUT recording when — prefill offers now() as a
        # starting point the user can correct before submit).
        if not self.instance.pk:
            self.initial["prepared_at"] = timezone.localtime()
        elif (
            not self.instance.fridge_entered_at
            and self.instance.status == "active"
            and not self.instance.first_fed_at
            and self.instance.prepared_at
            and (timezone.now() - self.instance.prepared_at)
            > timezone.timedelta(hours=2)
        ):
            # Bottle prepped >2h ago, never fed, never fridged — the
            # room-temp window is already expired; the honest prefill
            # for a still-active unit is that it went into the fridge
            # at some point. Offer now() as an editable default.
            self.initial["fridge_entered_at"] = timezone.localtime()

    def clean(self):
        cleaned = super().clean()
        pool = cleaned.get("source_pool")
        pfrom = cleaned.get("prepared_from")
        if pool and pfrom == "rtf_pour" and pool.form != "rtf":
            raise forms.ValidationError(
                _("Poured from RTF requires an RTF source pool.")
            )
        if pool and pfrom == "powder_mix" and pool.form != "powder":
            raise forms.ValidationError(
                _("Mixed from powder requires a powder source pool.")
            )
        return cleaned