# -*- coding: utf-8 -*-
from django_filters.rest_framework import DjangoFilterBackend


class FilterBackend(DjangoFilterBackend):
    """
    Filter backend that restores OpenAPI schema generation.

    django-filter removed its built-in schema generation methods in 25.1, in
    favour of ``drf-spectacular`` (see
    https://github.com/carltongibson/django-filter/blob/main/CHANGES.rst). The
    DRF OpenAPI schema generator, however, still calls
    ``get_schema_operation_parameters()`` on every configured filter backend,
    which makes the ``/api/schema`` endpoint and the ``generateschema``
    management command both fail with an ``AttributeError``.

    Re-implementing the method here keeps the filter query parameters that
    already exist in ``openapi-schema.yml`` in the generated schema, without
    depending on whether a filter backend happens to implement it.

    This is deliberately a stopgap, not a rejection of ``drf-spectacular``.
    Migrating the schema layer to it is worth doing, but it is a migration
    rather than a like-for-like swap: it renames every ``operationId`` in the
    published schema, moves every response body out of line into
    ``components/schemas``, and rejects the explicit
    ``AutoSchema(operation_id_base=...)`` set on ``api.views.ProfileView``.
    That belongs in a PR of its own. Until one lands, this subclass keeps the
    schema stable for anything already generating a client from
    ``openapi-schema.yml``, and it can be deleted wholesale afterwards.

    Adapted from django-filter 24.3's ``DjangoFilterBackend``, which is
    distributed under the BSD license, like Baby Buddy itself.
    """

    def get_schema_operation_parameters(self, view):
        """
        Return OpenAPI query parameters for the view's filter set.

        Field types are reported as strings, which matches both the historical
        django-filter behaviour and the existing committed schema.
        """
        try:
            queryset = view.get_queryset()
        except Exception:
            queryset = None

        filterset_class = self.get_filterset_class(view, queryset)
        if not filterset_class:
            return []

        parameters = []
        for field_name, field in filterset_class.base_filters.items():
            parameter = {
                "name": field_name,
                "required": field.extra["required"],
                "in": "query",
                "description": field.label if field.label is not None else field_name,
                "schema": {"type": "string"},
            }
            if field.extra and "choices" in field.extra:
                parameter["schema"]["enum"] = [c[0] for c in field.extra["choices"]]
            parameters.append(parameter)

        return parameters
