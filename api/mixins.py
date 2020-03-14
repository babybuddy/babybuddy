# -*- coding: utf-8 -*-
from collections import OrderedDict

from rest_framework.response import Response


class TimerFieldSupportMixin:
    def options(self, request, *args, **kwargs):
        """
        Add information about the optional "timer" field.
        """
        meta = self.metadata_class()
        data = meta.determine_metadata(request, self)
        post = data.get('actions').get('POST')  # type: OrderedDict
        post['timer'] = OrderedDict({
            "type": "integer",
            "required": False,
            "read_only": False,
            "label": "Timer",
            "details": "ID for an existing Timer, may be used in place of the "
                       "`start`, `end`, and/or `child` fields. "
        })
        details = "Required unless a value is provided in the `timer` field."
        post['child']['details'] = details
        post['start']['details'] = details
        post['end']['details'] = details
        return Response(data)
