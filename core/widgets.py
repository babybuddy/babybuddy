from django.forms import Media
from typing import Any, Dict, Optional
from django.forms import Widget

from . import models


class TagsEditor(Widget):
    class Media:
        js = ("babybuddy/js/tags_editor.js",)

    input_type = "hidden"
    template_name = "core/widget_tag_editor.html"

    @staticmethod
    def __unpack_tag(tag: models.Tag):
        return {"name": tag.name, "color": tag.color}

    def format_value(self, value: Any) -> Optional[str]:
        if value is not None and not isinstance(value, str):
            value = [self.__unpack_tag(tag) for tag in value]
        return value

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        class_string = attrs.get("class", "")
        class_string = class_string.replace("form-control", "")
        attrs["class"] = class_string + " babybuddy-tags-editor"
        return attrs

    def get_context(self, name: str, value: Any, attrs) -> Dict[str, Any]:
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
