import datetime

from django.forms import widgets


class DateTimeBaseInput(widgets.DateTimeBaseInput):
    def format_value(self, value):
        if isinstance(value, datetime.datetime):
            value = value.isoformat()
        return value


class DateTimeInput(DateTimeBaseInput):
    input_type = "datetime-local"

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        # Default to seconds granularity. Required for client validation in Safari.
        if "step" not in attrs:
            attrs["step"] = 1
        return attrs


class DateInput(DateTimeBaseInput):
    input_type = "date"


class TimeInput(DateTimeBaseInput):
    input_type = "time"


class TimeDurationInput(widgets.TimeInput):
    def __init__(self, attrs=None, format=None):
        super().__init__(attrs, format)
        self.attrs.update({"step": 1, "min": "00:00:00", "max": "23:59:59"})

    def format_value(self, value):
        if isinstance(value, datetime.timedelta):
            value = str(value)
        return value
