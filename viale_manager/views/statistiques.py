from datetime import date, timedelta

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View

from viale_manager.stats import presences, presences_chart, statistiques


def _date_param(request, name, default):
    try:
        return date.fromisoformat(request.GET.get(name, ''))
    except ValueError:
        return default


class _AdminPageView(View):
    admin_site = None

    def render(self, request, template, **context):
        return render(request, template, {**self.admin_site.each_context(request), **context})


class StatistiquesView(PermissionRequiredMixin, _AdminPageView):
    """Nuitées et revenus sur une période (par défaut l'année en cours)."""

    permission_required = 'viale_manager.view_statistiques'
    raise_exception = True

    def get(self, request):
        today = date.today()
        debut = _date_param(request, 'debut', today.replace(month=1, day=1))
        fin = _date_param(request, 'fin', today.replace(month=12, day=31))
        if fin < debut:
            debut, fin = fin, debut
        lignes, totaux = statistiques(debut, fin)
        page = Paginator(lignes, 50).get_page(request.GET.get('page'))
        return self.render(
            request, 'viale_manager/admin/statistiques.html',
            title='Statistiques', debut=debut, fin=fin, totaux=totaux, page=page,
        )


class PresencesView(PermissionRequiredMixin, _AdminPageView):
    """Présences, arrivées et départs par jour (par défaut les 7 prochains jours)."""

    permission_required = 'viale_manager.view_sejours'
    raise_exception = True

    def get(self, request):
        today = date.today()
        debut = _date_param(request, 'debut', today)
        fin = _date_param(request, 'fin', today + timedelta(days=6))
        if fin < debut:
            debut, fin = fin, debut
        # Au-delà, les barres deviennent illisibles.
        fin = min(fin, debut + timedelta(days=92))
        jours = presences(debut, fin)
        chart_data, chart_options = presences_chart(jours)
        return self.render(
            request, 'viale_manager/admin/presences.html',
            title='Présences', debut=debut, fin=fin, jours=jours,
            chart_data=chart_data, chart_options=chart_options,
        )
