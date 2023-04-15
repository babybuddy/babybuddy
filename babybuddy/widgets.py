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
