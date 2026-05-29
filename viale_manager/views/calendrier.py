from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from viale_manager.models import Sejours


def _get_sejours(start_str, end_str):
    if not start_str or not end_str:
        return Sejours.objects.none()
    return (
        Sejours.objects
        .select_related('visitor', 'reservation')
        .filter(arrival_date__lt=end_str[:10])
        .filter(departure_date__gte=start_str[:10])
        .exclude(departure_date__isnull=True)
        .order_by('arrival_date', 'visitor__nom')
    )


class CalendrierView(View):
    admin_site = None

    def get(self, request):
        context = {
            **self.admin_site.each_context(request),
            'title': 'Calendrier des séjours',
        }
        return render(request, 'viale_manager/admin/calendrier.html', context)


class CalendrierResourcesView(View):
    def get(self, request):
        qs = _get_sejours(request.GET.get('start', ''), request.GET.get('end', ''))
        qs = qs.select_related(None).select_related('visitor')
        resources = [{'id': str(s.id), 'title': str(s.visitor)} for s in qs]
        return JsonResponse(resources, safe=False)


class CalendrierEventsView(View):
    def get(self, request):
        qs = _get_sejours(request.GET.get('start', ''), request.GET.get('end', ''))
        events = []
        for s in qs:
            color = s.reservation.color
            events.append({
                'id': str(s.id),
                'resourceId': str(s.id),
                'title': str(s.visitor),
                'start': s.arrival_date.isoformat(),
                'end': (s.departure_date + timedelta(days=1)).isoformat(),
                'backgroundColor': color,
                'borderColor': color,
                'textColor': '#1a1a1a',
            })
        return JsonResponse(events, safe=False)
