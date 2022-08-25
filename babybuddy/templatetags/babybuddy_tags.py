# -*- coding: utf-8 -*-
import io
import base64
from multiprocessing.sharedctypes import Value

from django import template
from django.apps import apps
from django.utils import timezone
from django.utils.translation import to_locale, get_language
from django.template.defaultfilters import stringfilter

from core.models import Child

register = template.Library()


@register.simple_tag(takes_context=True)
def relative_url(context, field_name, value):
    """
    Create a relative URL with an updated field value.

    :param context: current request content.
    :param field_name: the field name to update.
    :param value: the new value for field_name.
    :return: encoded relative url with updated query string.
    """
    url = "?{}={}".format(field_name, value)
    querystring = context["request"].GET.urlencode().split("&")
    filtered_querystring = filter(lambda p: p.split("=")[0] != field_name, querystring)
    encoded_querystring = "&".join(filtered_querystring)
    return "{}&{}".format(url, encoded_querystring)


@register.simple_tag()
def version_string():
    """
    Get Baby Buddy's current version string.

    :return: version string ('n.n.n (commit)').
    """
    config = apps.get_app_config("babybuddy")
    return config.version_string


@register.simple_tag()
def get_current_locale():
    """
    Get the current language's locale code.

    :return: locale code (e.g. 'de', 'fr', etc.).
    """
    return to_locale(get_language())


@register.simple_tag()
def get_child_count():
    return Child.count()


@register.simple_tag()
def get_current_timezone():
    return timezone.get_current_timezone_name()


@register.simple_tag(takes_context=True)
def make_absolute_url(context, url):
    request = context["request"]
    abs_url = request.build_absolute_uri(url)
    return abs_url


class QrCodeNode(template.Node):
    def __init__(self, nodelist, strip, border, box_size) -> None:
        super().__init__()
        self.__nodelist = nodelist
        self.__strip = strip
        self.__border = border
        self.__box_size = box_size

    def render(self, context):
        contents = ""
        for node in self.__nodelist:
            contents += node.render(context)
        if self.__strip:
            contents = contents.strip()

        import qrcode

        qr = qrcode.QRCode(border=self.__border, box_size=self.__box_size)
        qr.add_data(contents)
        qr.make(fit=True)
        image = qr.make_image()

        bytesio = io.BytesIO()
        image.save(bytesio, format="png")
        base64_data = base64.b64encode(bytesio.getbuffer()).decode()
        return f"data:image/png;base64,{base64_data}"


@register.tag_function
def qrcodepng(parser, token):
    """
    This template tag allows the generation of arbirary qr code pngs that
    can be displayed, for example, in <img src="..."> html tags.

    The template tag can be used as follows:

    <img src="{% qrcodepng %}
        Hello world
    {% endqrcodepng %}">

    This will produce a qrcode that encodes the
    string "\n        Hello World\n    ". One can use the qrcode parameter
    ``stripwhitespace`` to strip the extra whitespace at the start and end of
    the string:

    {% qrcodepng stripwhitespace %}

    All supported arguments:

    - stripwhitespace: strip whitespace of the qrcode-contents
    - border=[int]: Border of the qrcode in pixels (default: 1)
    - box_size=[int]: Pixel size of the qr-code blocks (default: 5)
    """

    contents = token.split_contents()
    params = contents[1:]

    def get_parameter(name: str, value_type=None):
        search_for = name
        if value_type is not None:
            search_for += "="

        for p in params:
            if p.startswith(search_for):
                if value_type is None:
                    if p != search_for:
                        continue
                    params.remove(p)
                    return True
                else:
                    str_value = p[len(search_for) :]
                    try:
                        result = value_type(str_value)
                    except ValueError:
                        raise template.TemplateSyntaxError(
                            f"Invalid parameter '{p}' does "
                            f"not have type '{value_type}'"
                        )
                    else:
                        params.remove(p)
                        return result

        if value_type is None:
            return False
        return None

    strip = get_parameter("stripwhitespace")
    border = get_parameter("border", int) or 1
    box_size = get_parameter("box_size", int) or 5

    if params:
        raise template.TemplateSyntaxError(
            f"Unkown arguments for qrcode template tag: {', '.join(params)}"
        )

    nodelist = parser.parse(("endqrcodepng",))
    parser.delete_first_token()
    return QrCodeNode(nodelist, strip, border, box_size)
