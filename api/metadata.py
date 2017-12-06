# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import metadata


class APIMetadata(metadata.SimpleMetadata):
    """
    Custom metadata class for OPTIONS responses.
    """
    def determine_metadata(self, request, view):
        data = super(APIMetadata, self).determine_metadata(request, view)
        data.pop('description')
        if hasattr(view, 'filter_fields'):
            data.update({'filters': view.filter_fields})
        return data
