# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from typing import Optional

from django.db.models import Sum
from django.utils import timezone
from mcp_server import MCPToolset

from api.serializers import (
    ChildSerializer,
    DiaperChangeSerializer,
    FeedingSerializer,
    NoteSerializer,
    SleepSerializer,
    TemperatureSerializer,
    TimerSerializer,
    TummyTimeSerializer,
    WeightSerializer,
)
from core.models import (
    Child,
    DiaperChange,
    Feeding,
    Note,
    Sleep,
    Temperature,
    Timer,
    TummyTime,
    Weight,
)


def _serialize(serializer_class, instance):
    """Serialize a model instance using the corresponding DRF serializer."""
    return serializer_class(instance).data


def _serialize_many(serializer_class, queryset):
    """Serialize a queryset using the corresponding DRF serializer."""
    return serializer_class(queryset, many=True).data


def _get_child(slug):
    try:
        return Child.objects.get(slug=slug)
    except Child.DoesNotExist:
        raise ValueError(f"Child with slug '{slug}' not found.")


def _parse_date(date_str):
    if isinstance(date_str, date):
        return date_str
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _parse_datetime(dt_str):
    if isinstance(dt_str, datetime):
        if timezone.is_naive(dt_str):
            return timezone.make_aware(dt_str)
        return dt_str
    dt = datetime.fromisoformat(dt_str)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


class ChildTools(MCPToolset):
    """Tools for managing children."""

    def list_children(self) -> list[dict]:
        """List all children."""
        return _serialize_many(ChildSerializer, Child.objects.all())

    def get_child(self, slug: str) -> dict:
        """Get a child by slug."""
        return _serialize(ChildSerializer, _get_child(slug))

    def create_child(self, first_name: str, last_name: str, birth_date: str) -> dict:
        """Create a new child. birth_date format: YYYY-MM-DD."""
        child = Child(
            first_name=first_name,
            last_name=last_name,
            birth_date=_parse_date(birth_date),
        )
        child.full_clean()
        child.save()
        return _serialize(ChildSerializer, child)

    def update_child(
        self,
        slug: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        birth_date: Optional[str] = None,
    ) -> dict:
        """Update a child by slug. Only provided fields are updated."""
        child = _get_child(slug)
        if first_name is not None:
            child.first_name = first_name
        if last_name is not None:
            child.last_name = last_name
        if birth_date is not None:
            child.birth_date = _parse_date(birth_date)
        child.full_clean()
        child.save()
        return _serialize(ChildSerializer, child)

    def delete_child(self, slug: str) -> str:
        """Delete a child by slug."""
        child = _get_child(slug)
        child.delete()
        return f"Child '{slug}' deleted."


class FeedingTools(MCPToolset):
    """Tools for managing feedings."""

    def list_feedings(
        self,
        child_slug: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List feedings, optionally filtered by child slug and/or date (YYYY-MM-DD)."""
        qs = Feeding.objects.all()
        if child_slug:
            qs = qs.filter(child=_get_child(child_slug))
        if date:
            d = _parse_date(date)
            qs = qs.filter(start__date=d)
        return _serialize_many(FeedingSerializer, qs[:limit])

    def get_feeding(self, id: int) -> dict:
        """Get a feeding by ID."""
        try:
            return _serialize(FeedingSerializer, Feeding.objects.get(id=id))
        except Feeding.DoesNotExist:
            raise ValueError(f"Feeding with id {id} not found.")

    def log_feeding(
        self,
        child_slug: str,
        start: str,
        end: str,
        type: str,
        method: str,
        amount: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Log a new feeding. type: 'breast milk', 'formula', or 'fortified breast milk'.
        method: 'bottle', 'left breast', 'right breast', or 'both breasts'.
        start/end: ISO 8601 datetime strings."""
        child = _get_child(child_slug)
        feeding = Feeding(
            child=child,
            start=_parse_datetime(start),
            end=_parse_datetime(end),
            type=type,
            method=method,
            amount=amount,
            notes=notes,
        )
        feeding.full_clean()
        feeding.save()
        return _serialize(FeedingSerializer, feeding)

    def update_feeding(
        self,
        id: int,
        child_slug: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        type: Optional[str] = None,
        method: Optional[str] = None,
        amount: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Update a feeding by ID. Only provided fields are updated."""
        try:
            feeding = Feeding.objects.get(id=id)
        except Feeding.DoesNotExist:
            raise ValueError(f"Feeding with id {id} not found.")
        if child_slug is not None:
            feeding.child = _get_child(child_slug)
        if start is not None:
            feeding.start = _parse_datetime(start)
        if end is not None:
            feeding.end = _parse_datetime(end)
        if type is not None:
            feeding.type = type
        if method is not None:
            feeding.method = method
        if amount is not None:
            feeding.amount = amount
        if notes is not None:
            feeding.notes = notes
        feeding.full_clean()
        feeding.save()
        return _serialize(FeedingSerializer, feeding)

    def delete_feeding(self, id: int) -> str:
        """Delete a feeding by ID."""
        try:
            feeding = Feeding.objects.get(id=id)
        except Feeding.DoesNotExist:
            raise ValueError(f"Feeding with id {id} not found.")
        feeding.delete()
        return f"Feeding {id} deleted."


class DiaperChangeTools(MCPToolset):
    """Tools for managing diaper changes."""

    def list_diaper_changes(
        self,
        child_slug: Optional[str] = None,
        date: Optional[str] = None,
        wet: Optional[bool] = None,
        solid: Optional[bool] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List diaper changes with optional filters."""
        qs = DiaperChange.objects.all()
        if child_slug:
            qs = qs.filter(child=_get_child(child_slug))
        if date:
            d = _parse_date(date)
            qs = qs.filter(time__date=d)
        if wet is not None:
            qs = qs.filter(wet=wet)
        if solid is not None:
            qs = qs.filter(solid=solid)
        return _serialize_many(DiaperChangeSerializer, qs[:limit])

    def get_diaper_change(self, id: int) -> dict:
        """Get a diaper change by ID."""
        try:
            return _serialize(DiaperChangeSerializer, DiaperChange.objects.get(id=id))
        except DiaperChange.DoesNotExist:
            raise ValueError(f"DiaperChange with id {id} not found.")

    def log_diaper_change(
        self,
        child_slug: str,
        time: str,
        wet: bool,
        solid: bool,
        color: Optional[str] = None,
        amount: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Log a diaper change. At least one of wet/solid must be True.
        color: 'black', 'brown', 'green', or 'yellow'.
        time: ISO 8601 datetime string."""
        child = _get_child(child_slug)
        dc = DiaperChange(
            child=child,
            time=_parse_datetime(time),
            wet=wet,
            solid=solid,
            color=color or "",
            amount=amount,
            notes=notes,
        )
        dc.full_clean()
        dc.save()
        return _serialize(DiaperChangeSerializer, dc)

    def update_diaper_change(
        self,
        id: int,
        child_slug: Optional[str] = None,
        time: Optional[str] = None,
        wet: Optional[bool] = None,
        solid: Optional[bool] = None,
        color: Optional[str] = None,
        amount: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Update a diaper change by ID. Only provided fields are updated."""
        try:
            dc = DiaperChange.objects.get(id=id)
        except DiaperChange.DoesNotExist:
            raise ValueError(f"DiaperChange with id {id} not found.")
        if child_slug is not None:
            dc.child = _get_child(child_slug)
        if time is not None:
            dc.time = _parse_datetime(time)
        if wet is not None:
            dc.wet = wet
        if solid is not None:
            dc.solid = solid
        if color is not None:
            dc.color = color
        if amount is not None:
            dc.amount = amount
        if notes is not None:
            dc.notes = notes
        dc.full_clean()
        dc.save()
        return _serialize(DiaperChangeSerializer, dc)

    def delete_diaper_change(self, id: int) -> str:
        """Delete a diaper change by ID."""
        try:
            dc = DiaperChange.objects.get(id=id)
        except DiaperChange.DoesNotExist:
            raise ValueError(f"DiaperChange with id {id} not found.")
        dc.delete()
        return f"DiaperChange {id} deleted."


class SleepTools(MCPToolset):
    """Tools for managing sleep records."""

    def list_sleep(
        self,
        child_slug: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List sleep records, optionally filtered by child slug and/or date."""
        qs = Sleep.objects.all()
        if child_slug:
            qs = qs.filter(child=_get_child(child_slug))
        if date:
            d = _parse_date(date)
            qs = qs.filter(start__date=d)
        return _serialize_many(SleepSerializer, qs[:limit])

    def get_sleep(self, id: int) -> dict:
        """Get a sleep record by ID. Includes nap detection."""
        try:
            return _serialize(SleepSerializer, Sleep.objects.get(id=id))
        except Sleep.DoesNotExist:
            raise ValueError(f"Sleep with id {id} not found.")

    def log_sleep(
        self,
        child_slug: str,
        start: str,
        end: str,
        notes: Optional[str] = None,
    ) -> dict:
        """Log a sleep record. start/end: ISO 8601 datetime strings.
        Nap detection is automatic based on start time."""
        child = _get_child(child_slug)
        sleep = Sleep(
            child=child,
            start=_parse_datetime(start),
            end=_parse_datetime(end),
            notes=notes,
        )
        sleep.full_clean()
        sleep.save()
        return _serialize(SleepSerializer, sleep)

    def update_sleep(
        self,
        id: int,
        child_slug: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Update a sleep record by ID. Only provided fields are updated."""
        try:
            sleep = Sleep.objects.get(id=id)
        except Sleep.DoesNotExist:
            raise ValueError(f"Sleep with id {id} not found.")
        if child_slug is not None:
            sleep.child = _get_child(child_slug)
        if start is not None:
            sleep.start = _parse_datetime(start)
        if end is not None:
            sleep.end = _parse_datetime(end)
        if notes is not None:
            sleep.notes = notes
        sleep.full_clean()
        sleep.save()
        return _serialize(SleepSerializer, sleep)

    def delete_sleep(self, id: int) -> str:
        """Delete a sleep record by ID."""
        try:
            sleep = Sleep.objects.get(id=id)
        except Sleep.DoesNotExist:
            raise ValueError(f"Sleep with id {id} not found.")
        sleep.delete()
        return f"Sleep {id} deleted."


class TemperatureTools(MCPToolset):
    """Tools for managing temperature records."""

    def list_temperatures(
        self,
        child_slug: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List temperature records with optional filters."""
        qs = Temperature.objects.all()
        if child_slug:
            qs = qs.filter(child=_get_child(child_slug))
        if date:
            d = _parse_date(date)
            qs = qs.filter(time__date=d)
        return _serialize_many(TemperatureSerializer, qs[:limit])

    def get_temperature(self, id: int) -> dict:
        """Get a temperature record by ID."""
        try:
            return _serialize(TemperatureSerializer, Temperature.objects.get(id=id))
        except Temperature.DoesNotExist:
            raise ValueError(f"Temperature with id {id} not found.")

    def log_temperature(
        self,
        child_slug: str,
        temperature: float,
        time: str,
        notes: Optional[str] = None,
    ) -> dict:
        """Log a temperature reading. time: ISO 8601 datetime string."""
        child = _get_child(child_slug)
        temp = Temperature(
            child=child,
            temperature=temperature,
            time=_parse_datetime(time),
            notes=notes,
        )
        temp.full_clean()
        temp.save()
        return _serialize(TemperatureSerializer, temp)

    def update_temperature(
        self,
        id: int,
        child_slug: Optional[str] = None,
        temperature: Optional[float] = None,
        time: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Update a temperature record by ID."""
        try:
            temp = Temperature.objects.get(id=id)
        except Temperature.DoesNotExist:
            raise ValueError(f"Temperature with id {id} not found.")
        if child_slug is not None:
            temp.child = _get_child(child_slug)
        if temperature is not None:
            temp.temperature = temperature
        if time is not None:
            temp.time = _parse_datetime(time)
        if notes is not None:
            temp.notes = notes
        temp.full_clean()
        temp.save()
        return _serialize(TemperatureSerializer, temp)

    def delete_temperature(self, id: int) -> str:
        """Delete a temperature record by ID."""
        try:
            temp = Temperature.objects.get(id=id)
        except Temperature.DoesNotExist:
            raise ValueError(f"Temperature with id {id} not found.")
        temp.delete()
        return f"Temperature {id} deleted."


class WeightTools(MCPToolset):
    """Tools for managing weight records."""

    def list_weights(
        self,
        child_slug: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List weight records with optional child filter."""
        qs = Weight.objects.all()
        if child_slug:
            qs = qs.filter(child=_get_child(child_slug))
        return _serialize_many(WeightSerializer, qs[:limit])

    def get_weight(self, id: int) -> dict:
        """Get a weight record by ID."""
        try:
            return _serialize(WeightSerializer, Weight.objects.get(id=id))
        except Weight.DoesNotExist:
            raise ValueError(f"Weight with id {id} not found.")

    def log_weight(
        self,
        child_slug: str,
        weight: float,
        date: str,
        notes: Optional[str] = None,
    ) -> dict:
        """Log a weight measurement. date format: YYYY-MM-DD."""
        child = _get_child(child_slug)
        w = Weight(
            child=child,
            weight=weight,
            date=_parse_date(date),
            notes=notes,
        )
        w.full_clean()
        w.save()
        return _serialize(WeightSerializer, w)

    def update_weight(
        self,
        id: int,
        child_slug: Optional[str] = None,
        weight: Optional[float] = None,
        date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Update a weight record by ID."""
        try:
            w = Weight.objects.get(id=id)
        except Weight.DoesNotExist:
            raise ValueError(f"Weight with id {id} not found.")
        if child_slug is not None:
            w.child = _get_child(child_slug)
        if weight is not None:
            w.weight = weight
        if date is not None:
            w.date = _parse_date(date)
        if notes is not None:
            w.notes = notes
        w.full_clean()
        w.save()
        return _serialize(WeightSerializer, w)

    def delete_weight(self, id: int) -> str:
        """Delete a weight record by ID."""
        try:
            w = Weight.objects.get(id=id)
        except Weight.DoesNotExist:
            raise ValueError(f"Weight with id {id} not found.")
        w.delete()
        return f"Weight {id} deleted."


class TummyTimeTools(MCPToolset):
    """Tools for managing tummy time records."""

    def list_tummy_times(
        self,
        child_slug: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List tummy time records with optional filters."""
        qs = TummyTime.objects.all()
        if child_slug:
            qs = qs.filter(child=_get_child(child_slug))
        if date:
            d = _parse_date(date)
            qs = qs.filter(start__date=d)
        return _serialize_many(TummyTimeSerializer, qs[:limit])

    def get_tummy_time(self, id: int) -> dict:
        """Get a tummy time record by ID."""
        try:
            return _serialize(TummyTimeSerializer, TummyTime.objects.get(id=id))
        except TummyTime.DoesNotExist:
            raise ValueError(f"TummyTime with id {id} not found.")

    def log_tummy_time(
        self,
        child_slug: str,
        start: str,
        end: str,
        milestone: Optional[str] = None,
    ) -> dict:
        """Log a tummy time session. start/end: ISO 8601 datetime strings."""
        child = _get_child(child_slug)
        tt = TummyTime(
            child=child,
            start=_parse_datetime(start),
            end=_parse_datetime(end),
            milestone=milestone or "",
        )
        tt.full_clean()
        tt.save()
        return _serialize(TummyTimeSerializer, tt)

    def update_tummy_time(
        self,
        id: int,
        child_slug: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        milestone: Optional[str] = None,
    ) -> dict:
        """Update a tummy time record by ID."""
        try:
            tt = TummyTime.objects.get(id=id)
        except TummyTime.DoesNotExist:
            raise ValueError(f"TummyTime with id {id} not found.")
        if child_slug is not None:
            tt.child = _get_child(child_slug)
        if start is not None:
            tt.start = _parse_datetime(start)
        if end is not None:
            tt.end = _parse_datetime(end)
        if milestone is not None:
            tt.milestone = milestone
        tt.full_clean()
        tt.save()
        return _serialize(TummyTimeSerializer, tt)

    def delete_tummy_time(self, id: int) -> str:
        """Delete a tummy time record by ID."""
        try:
            tt = TummyTime.objects.get(id=id)
        except TummyTime.DoesNotExist:
            raise ValueError(f"TummyTime with id {id} not found.")
        tt.delete()
        return f"TummyTime {id} deleted."


class NoteTools(MCPToolset):
    """Tools for managing notes."""

    def list_notes(
        self,
        child_slug: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List notes with optional child filter."""
        qs = Note.objects.all()
        if child_slug:
            qs = qs.filter(child=_get_child(child_slug))
        return _serialize_many(NoteSerializer, qs[:limit])

    def get_note(self, id: int) -> dict:
        """Get a note by ID."""
        try:
            return _serialize(NoteSerializer, Note.objects.get(id=id))
        except Note.DoesNotExist:
            raise ValueError(f"Note with id {id} not found.")

    def create_note(
        self,
        child_slug: str,
        note: str,
    ) -> dict:
        """Create a note for a child."""
        child = _get_child(child_slug)
        n = Note(child=child, note=note)
        n.full_clean()
        n.save()
        return _serialize(NoteSerializer, n)

    def update_note(
        self,
        id: int,
        child_slug: Optional[str] = None,
        note: Optional[str] = None,
    ) -> dict:
        """Update a note by ID."""
        try:
            n = Note.objects.get(id=id)
        except Note.DoesNotExist:
            raise ValueError(f"Note with id {id} not found.")
        if child_slug is not None:
            n.child = _get_child(child_slug)
        if note is not None:
            n.note = note
        n.full_clean()
        n.save()
        return _serialize(NoteSerializer, n)

    def delete_note(self, id: int) -> str:
        """Delete a note by ID."""
        try:
            n = Note.objects.get(id=id)
        except Note.DoesNotExist:
            raise ValueError(f"Note with id {id} not found.")
        n.delete()
        return f"Note {id} deleted."


class TimerTools(MCPToolset):
    """Tools for managing timers."""

    def list_timers(
        self,
        active: Optional[bool] = None,
        child_slug: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """List timers with optional filters."""
        qs = Timer.objects.all()
        if active is not None:
            qs = qs.filter(active=active)
        if child_slug:
            qs = qs.filter(child=_get_child(child_slug))
        return _serialize_many(TimerSerializer, qs[:limit])

    def get_timer(self, id: int) -> dict:
        """Get a timer by ID."""
        try:
            return _serialize(TimerSerializer, Timer.objects.get(id=id))
        except Timer.DoesNotExist:
            raise ValueError(f"Timer with id {id} not found.")

    def start_timer(
        self,
        name: Optional[str] = None,
        child_slug: Optional[str] = None,
    ) -> dict:
        """Start a new timer. Optionally associate with a child and/or name."""
        child = _get_child(child_slug) if child_slug else None
        timer = Timer(
            user=self.request.user,
            name=name,
            child=child,
        )
        timer.full_clean()
        timer.save()
        return _serialize(TimerSerializer, timer)

    def stop_timer(self, id: int) -> dict:
        """Stop an active timer by ID. Returns the timer's details before stopping.
        Note: stopping a timer deletes it from the database."""
        try:
            timer = Timer.objects.get(id=id)
        except Timer.DoesNotExist:
            raise ValueError(f"Timer with id {id} not found.")
        if not timer.active:
            raise ValueError(f"Timer {id} is already stopped.")
        result = _serialize(TimerSerializer, timer)
        result["active"] = False
        result["duration"] = str(timezone.now() - timer.start)
        timer.stop()
        return result

    def restart_timer(self, id: int) -> dict:
        """Restart a timer by ID (resets start to now)."""
        try:
            timer = Timer.objects.get(id=id)
        except Timer.DoesNotExist:
            raise ValueError(f"Timer with id {id} not found.")
        timer.restart()
        return _serialize(TimerSerializer, timer)

    def delete_timer(self, id: int) -> str:
        """Delete a timer by ID."""
        try:
            timer = Timer.objects.get(id=id)
        except Timer.DoesNotExist:
            raise ValueError(f"Timer with id {id} not found.")
        timer.delete()
        return f"Timer {id} deleted."


class DailySummaryTools(MCPToolset):
    """Tools for daily summaries."""

    def get_daily_summary(self, child_slug: str, date: Optional[str] = None) -> dict:
        """Get a daily summary for a child on a given date (default: today).
        Returns feeding count/total amount, diaper change counts, sleep
        duration, and last events."""
        child = _get_child(child_slug)
        d = _parse_date(date) if date else timezone.localdate()

        # Feedings
        feedings = Feeding.objects.filter(child=child, start__date=d)
        feeding_count = feedings.count()
        feeding_amount = feedings.aggregate(total=Sum("amount"))["total"] or 0

        # Diaper changes
        changes = DiaperChange.objects.filter(child=child, time__date=d)
        diaper_count = changes.count()
        diaper_wet = changes.filter(wet=True).count()
        diaper_solid = changes.filter(solid=True).count()

        # Sleep
        sleep_entries = Sleep.objects.filter(child=child, start__date=d)
        sleep_total = timedelta()
        nap_total = timedelta()
        nap_count = 0
        for s in sleep_entries:
            if s.duration:
                sleep_total += s.duration
                if s.nap:
                    nap_total += s.duration
                    nap_count += 1

        # Tummy time
        tummy_entries = TummyTime.objects.filter(child=child, start__date=d)
        tummy_total = timedelta()
        tummy_count = tummy_entries.count()
        for tt in tummy_entries:
            if tt.duration:
                tummy_total += tt.duration

        # Last events
        last_feeding = Feeding.objects.filter(child=child).first()
        last_change = DiaperChange.objects.filter(child=child).first()
        last_sleep = Sleep.objects.filter(child=child).first()

        return {
            "child": _serialize(ChildSerializer, child),
            "date": str(d),
            "feeding": {
                "count": feeding_count,
                "total_amount": feeding_amount,
                "last": (
                    _serialize(FeedingSerializer, last_feeding)
                    if last_feeding
                    else None
                ),
            },
            "diaper_changes": {
                "count": diaper_count,
                "wet": diaper_wet,
                "solid": diaper_solid,
                "last": (
                    _serialize(DiaperChangeSerializer, last_change)
                    if last_change
                    else None
                ),
            },
            "sleep": {
                "total_duration": str(sleep_total),
                "nap_count": nap_count,
                "nap_duration": str(nap_total),
                "last": (
                    _serialize(SleepSerializer, last_sleep) if last_sleep else None
                ),
            },
            "tummy_time": {
                "count": tummy_count,
                "total_duration": str(tummy_total),
            },
        }
