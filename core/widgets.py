import datetime
from typing import Any, Dict, Optional

from django.forms import RadioSelect, widgets

from . import models


class TagsEditor(widgets.Widget):
    """
    Custom widget that provides an alternative editor for tags provided by the
    taggit library.

    The widget makes use of bootstrap v4 and its badge/pill feature and renders
    a list of tags as badges that can be clicked to remove or add a tag to
    the list of set tags. In addition, a user can dynamically add new, custom
    tags, using a text editor.
    """

    class Media:
        js = ("babybuddy/js/tags_editor.js",)

    input_type = "hidden"
    template_name = "core/widget_tag_editor.html"

    @staticmethod
    def __unpack_tag(tag: models.Tag):
        """
        Tiny utility function used to translate a tag to a serializable
        dictionary of strings.
        """
        return {"name": tag.name, "color": tag.color}

    def format_value(self, value: Any) -> Optional[str]:
        """
        Override format_value to provide a list of dictionaries rather than
        a flat, comma-separated list of tags. This allows for the more
        complex rendering of tags provided by this plugin.
        """
        if value is not None and not isinstance(value, str):
            value = [self.__unpack_tag(tag) for tag in value]
        return value

    def build_attrs(self, base_attrs, extra_attrs=None):
        """
        Bootstrap integration adds form-control to the classes of the widget.
        This works only for "plain" input-based widgets however. In addition,
        we need to add a custom class "babybuddy-tags-editor" for the javascript
        file to detect the widget and take control of its contents.
        """
        attrs = super().build_attrs(base_attrs, extra_attrs)
        class_string = attrs.get("class", "")
        class_string = class_string.replace("form-control", "")
        attrs["class"] = class_string + " babybuddy-tags-editor"
        return attrs

    def get_context(self, name: str, value: Any, attrs) -> Dict[str, Any]:
        """
        Adds extra information to the payload provided to the widget's template.

        Specifically:
        - Query a list if "recently used" tags (max 256 to not cause
          DoS issues) from the database to be used for auto-completion. ("most")
        - Query a smaller list of 5 tags to be made available from a quick
          selection widget ("quick").
        """
        most_tags = models.Tag.objects.order_by("-last_used").all()[:256]

        result = super().get_context(name, value, attrs)

        tag_names = set(
            x["name"] for x in (result.get("widget", {}).get("value", None) or [])
        )
        quick_suggestion_tags = [t for t in most_tags if t.name not in tag_names][:5]

        result["widget"]["tag_suggestions"] = {
            "quick": [
                self.__unpack_tag(t)
                for t in quick_suggestion_tags
                if t.name not in tag_names
            ],
            "most": [self.__unpack_tag(t) for t in most_tags],
        }
        return result


class ChildRadioSelect(RadioSelect):
    input_type = "radio"
    template_name = "core/child_radio.html"
    option_template_name = "core/child_radio_option.html"
    attrs = {"class": "btn-check"}

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["class"] += " btn-check"
        return attrs

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        if value != "":
            option["picture"] = value.instance.picture
        return option


class PillRadioSelect(RadioSelect):
    input_type = "radio"
    template_name = "core/pill_radio.html"
    option_template_name = "core/pill_radio_option.html"

    attrs = {"class": "btn-check"}

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["class"] += " btn-check"
        return attrs
