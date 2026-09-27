import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST

from viale_manager.models import AssignationsMaisonnees, Houses, MaisonneesPlanning


def _board_url(planning):
    return reverse('viale_manager:viale_manager_maisonnees', args=[planning.id])


def _age(naissance, jour):
    if not naissance:
        return None
    return jour.year - naissance.year - ((jour.month, jour.day) < (naissance.month, naissance.day))


class MaisonneesView(PermissionRequiredMixin, View):
    """Tableau des maisonnées : une colonne « à placer » puis une par maison du planning."""

    admin_site = None
    permission_required = 'viale_manager.view_maisonneesplanning'
    raise_exception = True

    def get(self, request, pk=None):
        a_venir = MaisonneesPlanning.objects.filter(end__gte=date.today()).order_by('end')
        if pk is None:
            planning = a_venir.first()
            if planning:
                return redirect(_board_url(planning))
        else:
            planning = get_object_or_404(MaisonneesPlanning, pk=pk)

        context = {
            **self.admin_site.each_context(request),
            'title': f'Maisonnées {planning}' if planning else 'Maisonnées',
            'planning': planning,
            'plannings': a_venir,
            'maisons': Houses.objects.filter(community=True).order_by('name'),
            'next_begin': MaisonneesPlanning.next_period()[0],
            'next_end': MaisonneesPlanning.next_period()[1],
        }
        if planning:
            planning.prepare()
            assignations = (
                planning.assignationsmaisonnees_set
                .select_related('sejour__visitor')
                .order_by('sejour__visitor__nom', 'sejour__visitor__prenom')
            )
            houses = list(planning.houses.filter(community=True).order_by('name'))
            colonnes = {h.id: [] for h in houses}
            a_placer = []
            for a in assignations:
                a.age = _age(a.sejour.visitor.date_de_naissance, planning.begin)
                colonnes.get(a.house_id, a_placer).append(a)
            context['colonnes'] = [(None, 'À placer', a_placer)] + [(h.id, h.name, colonnes[h.id]) for h in houses]
            context['houses_ids'] = [h.id for h in houses]
        return render(request, 'viale_manager/admin/maisonnees.html', context)


def _maisons_postees(request):
    return Houses.objects.filter(community=True, id__in=request.POST.getlist('houses'))


@require_POST
@permission_required('viale_manager.add_maisonneesplanning', raise_exception=True)
def maisonnees_create(request):
    try:
        begin = date.fromisoformat(request.POST.get('begin', ''))
        end = date.fromisoformat(request.POST.get('end', ''))
    except ValueError:
        messages.error(request, "Dates invalides.")
        return redirect('viale_manager:viale_manager_maisonnees_index')
    if end < begin:
        messages.error(request, "La fin doit être après le début.")
        return redirect('viale_manager:viale_manager_maisonnees_index')
    planning = MaisonneesPlanning.objects.create(begin=begin, end=end)
    planning.set_houses(_maisons_postees(request))
    return redirect(_board_url(planning))


@require_POST
@permission_required('viale_manager.change_maisonneesplanning', raise_exception=True)
def maisonnees_houses(request, pk):
    planning = get_object_or_404(MaisonneesPlanning, pk=pk)
    planning.set_houses(_maisons_postees(request))
    messages.success(request, "Maisons du planning mises à jour.")
    return redirect(_board_url(planning))


@require_POST
@permission_required('viale_manager.change_maisonneesplanning', raise_exception=True)
def maisonnees_reset(request, pk):
    planning = get_object_or_404(MaisonneesPlanning, pk=pk)
    planning.reset()
    messages.warning(request, "Répartition remise à zéro.")
    return redirect(_board_url(planning))


@require_POST
@permission_required('viale_manager.change_assignationsmaisonnees', raise_exception=True)
def maisonnees_assign(request, pk):
    """Déplace une personne (appel JSON du glisser-déposer). ``house`` nul = « à placer »."""
    planning = get_object_or_404(MaisonneesPlanning, pk=pk)
    try:
        payload = json.loads(request.body)
    except ValueError:
        return JsonResponse({'ok': False}, status=400)
    assignation = get_object_or_404(AssignationsMaisonnees, pk=payload.get('assignation'), planning=planning)
    house_id = payload.get('house')
    if house_id is not None and not planning.houses.filter(id=house_id).exists():
        return JsonResponse({'ok': False}, status=400)
    assignation.house_id = house_id
    assignation.save(update_fields=['house'])
    return JsonResponse({'ok': True})
