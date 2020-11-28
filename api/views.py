# -*- coding: utf-8 -*-
from django.db.models import Sum
from django.utils import timezone

from rest_framework import views, viewsets
from rest_framework.response import Response

from core import models

from . import serializers
from .mixins import TimerFieldSupportMixin


class ChildViewSet(viewsets.ModelViewSet):
    queryset = models.Child.objects.all()
    serializer_class = serializers.ChildSerializer
    lookup_field = 'slug'
    filterset_fields = ('first_name', 'last_name', 'slug')


class ChildDashboardAPIView(views.APIView):
    queryset = models.Child.objects.none()  # Required for DjangoModelPermissions
    serializer_class = serializers.ChildDashboardSerializer

    def get(self, request, slug):
        child = models.Child.objects.get(slug=slug)
        date = timezone.localtime().date()

        data = {
            'child': child,
            'feedings': {'last': {}, 'methods': [], 'today': {}},
            'sleep': {'last': {}, 'today_sleep': {}, 'today_naps': {}},
            'tummy_times': {'today_stats': {}, 'today_times': [], 'last': {}},
        }

        # Feedings.
        feedings = models.Feeding.objects.filter(child=child)
        data['feedings']['last'] = serializers.FeedingSerializer(
            feedings.order_by('-end').first()).data
        data['feedings']['methods'] = [feeding.method for feeding in feedings.order_by('-end')[:3]]
        feedings_today = feedings.filter(
            start__year=date.year,
            start__month=date.month,
            start__day=date.day) | feedings.filter(
            end__year=date.year,
            end__month=date.month,
            end__day=date.day)
        data['feedings']['today'] = {
            'total': sum([instance.amount for instance in feedings_today if instance.amount]),
            'count': len(feedings_today)}

        # Sleep.
        sleep = models.Sleep.objects.filter(child=child)
        data['sleep']['last'] = serializers.SleepSerializer(
            sleep.order_by('-end').first()).data
        sleep_today = sleep.filter(
            start__year=date.year,
            start__month=date.month,
            start__day=date.day) | sleep.filter(
            end__year=date.year,
            end__month=date.month,
            end__day=date.day)
        total = timezone.timedelta(seconds=0)
        for instance in sleep_today:
            start = timezone.localtime(instance.start)
            end = timezone.localtime(instance.end)
            # Account for dates crossing midnight.
            if start.date() != date:
                start = start.replace(year=end.year, month=end.month, day=end.day,
                                      hour=0, minute=0, second=0)
            total += end - start
        count = len(sleep_today)
        data['sleep']['today_sleep'] = {'total': total.total_seconds(),
                                        'count': count}
        naps = models.Sleep.naps.filter(child=child)
        naps_today = naps.filter(
            start__year=date.year,
            start__month=date.month,
            start__day=date.day) | naps.filter(child=child).filter(
            end__year=date.year,
            end__month=date.month,
            end__day=date.day)
        data['sleep']['today_naps'] = {
            'total': naps_today.aggregate(Sum('duration'))['duration__sum'].total_seconds(),
            'count': len(naps_today)}

        # Tummy times
        tummy_time = models.TummyTime.objects.filter(
            child=child, end__year=date.year, end__month=date.month,
            end__day=date.day).order_by('-end')
        stats = {
            'total': timezone.timedelta(seconds=0),
            'count': tummy_time.count()
        }
        for instance in tummy_time:
            stats['total'] += timezone.timedelta(seconds=instance.duration.seconds)
        stats['total'] = stats['total'].total_seconds()
        data['tummy_times'] = {
            'today_stats': stats,
            'today_times': serializers.TummyTimeSerializer(tummy_time, many=True).data,
            'last': serializers.TummyTimeSerializer(tummy_time.first()).data}

        results = serializers.ChildDashboardSerializer(instance=data).data

        return Response(results)


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = models.DiaperChange.objects.all()
    serializer_class = serializers.DiaperChangeSerializer
    filterset_fields = ('child', 'wet', 'solid', 'color', 'amount')


class FeedingViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.Feeding.objects.all()
    serializer_class = serializers.FeedingSerializer
    filterset_fields = ('child', 'type', 'method')


class NoteViewSet(viewsets.ModelViewSet):
    queryset = models.Note.objects.all()
    serializer_class = serializers.NoteSerializer
    filterset_fields = ('child',)


class SleepViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.Sleep.objects.all()
    serializer_class = serializers.SleepSerializer
    filterset_fields = ('child',)


class TemperatureViewSet(viewsets.ModelViewSet):
    queryset = models.Temperature.objects.all()
    serializer_class = serializers.TemperatureSerializer
    filterset_fields = ('child',)


class TimerViewSet(viewsets.ModelViewSet):
    queryset = models.Timer.objects.all()
    serializer_class = serializers.TimerSerializer
    filterset_fields = ('child', 'active', 'user')


class TummyTimeViewSet(TimerFieldSupportMixin, viewsets.ModelViewSet):
    queryset = models.TummyTime.objects.all()
    serializer_class = serializers.TummyTimeSerializer
    filterset_fields = ('child',)


class WeightViewSet(viewsets.ModelViewSet):
    queryset = models.Weight.objects.all()
    serializer_class = serializers.WeightSerializer
    filterset_fields = ('child',)
