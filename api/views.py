# -*- coding: utf-8 -*-
from django.db.models import Q, Sum
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
        time = timezone.datetime.combine(date, timezone.localtime().min.time())
        time = timezone.make_aware(time)

        data = {
            'child': child,
            'diaper_changes': {'last': {}, 'past_week': []},
            'feedings': {'last': {}, 'methods': [], 'today': {}},
            'sleep': {'last': {}, 'today_sleep': {}, 'today_naps': {}},
            'timers': [],
            'tummy_times': {'today_stats': {}, 'today_times': [], 'last': {}},
        }

        # Diaper changes.
        changes = models.DiaperChange.objects.filter(child=child)
        data['diaper_changes']['last'] = serializers.DiaperChangeSerializer(
            changes.order_by('-time').first()).data
        stats = {}
        week_total = 0
        max_date = (time + timezone.timedelta(days=1)).replace(
            hour=0, minute=0, second=0)
        min_date = (max_date - timezone.timedelta(days=7)).replace(
            hour=0, minute=0, second=0)
        for x in range(7):
            stats[x] = {'wet': 0.0, 'solid': 0.0}
        instances = changes.filter(time__gt=min_date).filter(
            time__lt=max_date).order_by('-time')
        for instance in instances:
            key = (max_date - instance.time).days
            if instance.wet:
                stats[key]['wet'] += 1
            if instance.solid:
                stats[key]['solid'] += 1
        for key, info in stats.items():
            total = info['wet'] + info['solid']
            week_total += total
            if total > 0:
                stats[key]['wet_pct'] = info['wet'] / total * 100
                stats[key]['solid_pct'] = info['solid'] / total * 100
        data['diaper_changes']['past_week'] = {'stats': stats, 'total': week_total}

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
        naps_sum_time = naps_today.aggregate(Sum('duration'))['duration__sum']
        data['sleep']['today_naps'] = {
            'total': naps_sum_time.total_seconds() if naps_sum_time else 0,
            'count': len(naps_today)}

        # Timers
        timers = models.Timer.objects.filter(
            Q(active=True),
            Q(child=child) | Q(child=None)
        ).order_by('-start')
        data['timers'] = serializers.TimerSerializer(timers, many=True).data

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
