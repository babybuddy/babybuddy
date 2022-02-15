from typing import Any, Dict, Optional
from django.forms import Widget

class TagsEditor(Widget):
    input_type = 'hidden'
    template_name = 'core/widget_tag_editor.html'

    @staticmethod
    def __unpack_tag(tag):
        return {'name': tag.name, 'color': tag.color}

    def format_value(self, value: Any) -> Optional[str]:
        if value is not None and not isinstance(value, str):
            value = [self.__unpack_tag(tag) for tag in value]
        return value
    
    def get_context(self, name: str, value: Any, attrs) -> Dict[str, Any]:
        from . import models

        most_tags = models.BabyBuddyTag.objects.order_by(
            '-last_used'
        ).all()[:256]
        quick_suggestion_tags = models.BabyBuddyTag.objects.order_by(
            '-last_used'
        ).all()

        result = super().get_context(name, value, attrs)

        tag_names = set(x['name'] for x in result['widget']['value'])
        quick_suggestion_tags = [
            t for t in quick_suggestion_tags
            if t.name not in tag_names
        ][:5]

        result['widget']['tag_suggestions'] = {
            'quick': [
                self.__unpack_tag(t) for t in quick_suggestion_tags
                if t.name not in tag_names
            ],
            'most': [
                self.__unpack_tag(t) for t in most_tags
            ]
        }
        return result