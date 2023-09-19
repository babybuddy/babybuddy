from django import template

from core.models import Child

register = template.Library()


@register.inclusion_tag("core/child_quick_switch.html")
def child_quick_switch(current_child, target_url):
    children = Child.objects.exclude(slug=current_child.slug)

    return {
        "children": children,
        "current_child": current_child,
        "target_url": target_url,
    }
