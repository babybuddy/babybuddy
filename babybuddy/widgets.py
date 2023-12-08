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
        # Default to seconds granularity. Required for client validation in
        # Safari.
        if "step" not in attrs:
            attrs["step"] = 1
        return attrs


class CopyPasteDateInput(DateTimeInput):
    template_name = "babybuddy/form_widget_copy_paste_date.html"


class DateInput(DateTimeBaseInput):
    input_type = "date"


class StartEndDateTimeInput(widgets.MultiWidget):
    def __init__(self, attrs=None):
        super(StartEndDateTimeInput, self).__init__(
            # Add classes here because widget_tweaks can't do it directly to a
            # subwidget in a multiwidget field.
            [
                CopyPasteDateInput(attrs={"class": "form-control"}),
                CopyPasteDateInput(attrs={"class": "form-control"}),
            ],
            attrs,
        )

    def subwidgets(self, name, value, attrs=None):
        context = self.get_context(name, value, attrs)
        return context["widget"]["subwidgets"]

    def decompress(self, value):
        if value:
            return value
        else:
            return ["", ""]


class TimeInput(DateTimeBaseInput):
    input_type = "time"
