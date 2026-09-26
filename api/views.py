# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import mixins, status, viewsets, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from core import models
from babybuddy import models as babybuddy_models
from webhooks import models as webhooks_models

from . import serializers, filters


class BMIViewSet(viewsets.ModelViewSet):
    queryset = models.BMI.objects.all()
    serializer_class = serializers.BMISerializer
    filterset_fields = ("child", "date")
    ordering_fields = ("child", "date")
    ordering = "-date"

    def get_view_name(self):
        """
        Gets the view name without changing the case of the model verbose name.
        """
        name = models.BMI._meta.verbose_name
        if self.suffix:
            name += " " + self.suffix
        return name


class ChildViewSet(viewsets.ModelViewSet):
    queryset = models.Child.objects.all()
    serializer_class = serializers.ChildSerializer
    lookup_field = "slug"
    filterset_fields = (
        "id",
        "first_name",
        "last_name",
        "slug",
        "birth_date",
        "birth_time",
    )
    ordering_fields = ("birth_date", "birth_time", "first_name", "last_name", "slug")
    ordering = ["-birth_date", "-birth_time"]


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = models.DiaperChange.objects.all()
    serializer_class = serializers.DiaperChangeSerializer
    filterset_class = filters.DiaperChangeFilter
    ordering_fields = ("amount", "time")
    ordering = "-time"


class FeedingViewSet(viewsets.ModelViewSet):
    queryset = models.Feeding.objects.all()
    serializer_class = serializers.FeedingSerializer
    filterset_class = filters.FeedingFilter
    ordering_fields = ("amount", "duration", "end", "start")
    ordering = "-end"


class HeadCircumferenceViewSet(viewsets.ModelViewSet):
    queryset = models.HeadCircumference.objects.all()
    serializer_class = serializers.HeadCircumferenceSerializer
    filterset_fields = ("child", "date")
    ordering_fields = ("date", "head_circumference")
    ordering = "-date"


class HeightViewSet(viewsets.ModelViewSet):
    queryset = models.Height.objects.all()
    serializer_class = serializers.HeightSerializer
    filterset_fields = ("child", "date")
    ordering_fields = ("date", "height")
    ordering = "-date"


class MedicationViewSet(viewsets.ModelViewSet):
    queryset = models.Medication.objects.all()
    serializer_class = serializers.MedicationSerializer
    filterset_class = filters.MedicationFilter
    ordering_fields = ("time", "name", "dosage")
    ordering = "-time"

    def get_view_name(self):
        # Use model's verbose_name for consistency with user-facing strings
        name = self.queryset.model._meta.verbose_name
        suffix = getattr(self, "suffix", None)
        if suffix:
            name = f"{name} {suffix}"
        return name


class NoteViewSet(viewsets.ModelViewSet):
    queryset = models.Note.objects.all()
    serializer_class = serializers.NoteSerializer
    filterset_class = filters.NoteFilter
    ordering_fields = "time"
    ordering = "-time"


class PumpingViewSet(viewsets.ModelViewSet):
    queryset = models.Pumping.objects.all()
    serializer_class = serializers.PumpingSerializer
    filterset_class = filters.PumpingFilter
    ordering_fields = ("amount", "duration", "end", "start")
    ordering = "-end"


class SleepViewSet(viewsets.ModelViewSet):
    queryset = models.Sleep.objects.all()
    serializer_class = serializers.SleepSerializer
    filterset_class = filters.SleepFilter
    ordering_fields = ("duration", "end", "start")
    ordering = "-end"


class TagViewSet(viewsets.ModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    lookup_field = "slug"
    filterset_fields = ("last_used", "name")
    ordering_fields = ("last_used", "name", "slug")
    ordering = "name"


class TemperatureViewSet(viewsets.ModelViewSet):
    queryset = models.Temperature.objects.all()
    serializer_class = serializers.TemperatureSerializer
    filterset_class = filters.TemperatureFilter
    ordering_fields = ("temperature", "time")
    ordering = "-time"


class TimerViewSet(viewsets.ModelViewSet):
    queryset = models.Timer.objects.all()
    serializer_class = serializers.TimerSerializer
    filterset_class = filters.TimerFilter
    ordering_fields = ("duration", "end", "start")
    ordering = "-start"

    @action(detail=True, methods=["patch"])
    def restart(self, request, pk=None):
        timer = self.get_object()
        timer.restart()
        return Response(self.serializer_class(timer).data)


class TummyTimeViewSet(viewsets.ModelViewSet):
    queryset = models.TummyTime.objects.all()
    serializer_class = serializers.TummyTimeSerializer
    filterset_class = filters.TummyTimeFilter
    ordering_fields = ("duration", "end", "start")
    ordering = "-start"


class WeightViewSet(viewsets.ModelViewSet):
    queryset = models.Weight.objects.all()
    serializer_class = serializers.WeightSerializer
    filterset_fields = ("child", "date")
    ordering_fields = ("date", "weight")
    ordering = "-date"


class ProfileView(views.APIView):
    schema = AutoSchema(operation_id_base="CurrentProfile")

    action = "get"
    basename = "profile"

    queryset = babybuddy_models.Settings.objects.all()
    serializer_class = serializers.ProfileSerializer

    def get(self, request):
        settings = get_object_or_404(
            babybuddy_models.Settings.objects, user=request.user
        )
        serializer = self.serializer_class(settings)
        return Response(serializer.data)


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    queryset = webhooks_models.WebhookEndpoint.objects.all()
    serializer_class = serializers.WebhookEndpointSerializer
    filterset_fields = ("active",)
    ordering_fields = ("name", "created", "last_delivery")
    ordering = "name"

    def create(self, request, *args, **kwargs):
        """
        Create an endpoint and return its secret this one time, since the
        secret is never part of a response afterwards.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        endpoint = serializer.save()
        data = dict(serializer.data, secret=endpoint.secret)
        return Response(
            data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )


class CaregiverViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Caregiver accounts only. Accounts in any other role, and anything with
    staff or superuser status, are not reachable here at all. There is no
    delete; access is withdrawn by setting `is_active` to false, the same way
    the user guide already tells an administrator to withdraw it.
    """

    serializer_class = serializers.CaregiverSerializer
    filterset_fields = ("is_active",)
    ordering_fields = ("username", "date_joined")
    ordering = "username"

    def get_queryset(self):
        return (
            get_user_model()
            .objects.filter(
                groups__name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"],
                is_staff=False,
                is_superuser=False,
            )
            .select_related("settings")
        )

    def create(self, request, *args, **kwargs):
        """
        Create a caregiver and return their API key this one time.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = dict(serializer.data, api_key=user.settings.api_key().key)
        return Response(
            data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )
