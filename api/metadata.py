# -*- coding: utf-8 -*-
from rest_framework import metadata


class APIMetadata(metadata.SimpleMetadata):
    """
    Custom metadata class for OPTIONS responses.
    """

    def determine_metadata(self, request, view):
        data = super(APIMetadata, self).determine_metadata(request, view)
        data.pop("description")
        if hasattr(view, "filterset_fields"):
            data.update({"filters": view.filterset_fields})
        elif hasattr(view, "filterset_class"):
            data.update({"filters": view.filterset_class.Meta.fields})
        return data
