from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from icalendar import Calendar, Event

from core.models import Reunion


def reunion_ical(request, pk):
    reunion = get_object_or_404(Reunion.objects.select_related('organe', 'adresse'), pk=pk)

    cal = Calendar()
    cal.add('prodid', '-//dj-asbl//FR')
    cal.add('version', '2.0')

    event = Event()
    event.add('summary', str(reunion))
    event.add('dtstart', reunion.debut)
    event.add('dtend', reunion.fin or reunion.debut)
    event.add('uid', f'reunion-{reunion.pk}@dj-asbl')

    if reunion.adresse:
        location = f"{reunion.adresse.adresse}, {reunion.adresse.code_postal} {reunion.adresse.ville}"
        event.add('location', location)

    cal.add_component(event)

    response = HttpResponse(cal.to_ical(), content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="reunion-{reunion.pk}.ics"'
    return response