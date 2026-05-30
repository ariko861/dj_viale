from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.widgets import UnfoldBooleanSwitchWidget

from viale_manager.forms import ReservationLinkForm
from viale_manager.models import Reservations


def _label(text, variant, icon=None, title=None):
    """Badge coloré Unfold (helper label.html)."""
    return render_to_string('unfold/helpers/label.html', {
        'text': text, 'variant': variant, 'icon': icon, 'label_title': title,
    })


def _bool_label(value, true_text, false_text):
    if value:
        return _label(true_text, 'success', icon='check')
    return _label(false_text, 'danger', icon='close')


def _id_cell(rid, public_url):
    return format_html(
        '<button type="button" class="text-left group cursor-pointer" onclick="vmCopyLink(this, \'{}\')">'
        '<span class="font-semibold text-primary-600">{}</span><br>'
        '<span class="copy-lbl text-[11px] text-base-400 group-hover:text-primary-600">Cliquez pour copier le lien</span>'
        '</button>',
        public_url, rid,
    )


def _toggle_cell(url, csrf, sent):
    switch = UnfoldBooleanSwitchWidget().render(
        'link_sent', sent, attrs={'onchange': 'this.form.submit()', 'title': 'Basculer « lien envoyé »'},
    )
    return format_html(
        '<form method="post" action="{}" class="inline">'
        '<input type="hidden" name="csrfmiddlewaretoken" value="{}">{}'
        '</form>',
        url, csrf, switch,
    )


def _check_cross(value):
    if value:
        return mark_safe('<span class="material-symbols-outlined text-green-600">check</span>')
    return mark_safe('<span class="material-symbols-outlined text-red-500">close</span>')


def _actions_cell(public_url, edit_url, delete_url, csrf):
    return format_html(
        '<div class="flex items-center gap-1 justify-end">'
        '<a href="{}" target="_blank" title="Ouvrir le formulaire" '
        'class="material-symbols-outlined text-base-400 hover:text-primary-600">open_in_new</a>'
        '<a href="{}" title="Modifier les paramètres" '
        'class="material-symbols-outlined text-base-400 hover:text-primary-600">edit</a>'
        '<form method="post" action="{}" class="inline" '
        'onsubmit="return confirm(\'Supprimer cette réservation et ses séjours ?\');">'
        '<input type="hidden" name="csrfmiddlewaretoken" value="{}">'
        '<button type="submit" title="Supprimer" '
        'class="material-symbols-outlined text-base-400 hover:text-red-500 cursor-pointer">delete</button>'
        '</form></div>',
        public_url, edit_url, delete_url, csrf,
    )


def reservations_widget_context(request, limit=8):
    """Contexte du widget de gestion des liens de réservation.

    Construit un dict ``table`` consommé par le composant Unfold
    ``unfold/components/table.html``. Réutilisé dans l'index admin et
    au-dessus de la liste des séjours.
    """
    csrf = get_token(request)
    rows = []
    for r in Reservations.objects.order_by('-id')[:limit]:
        public_url = request.build_absolute_uri(reverse('reservation_form', args=[r.link_token]))
        edit_url = reverse('viale_manager:viale_manager_reservations_change', args=[r.id])
        toggle_url = reverse('viale_manager:viale_manager_reservation_toggle_link_sent', args=[r.id])
        delete_url = reverse('viale_manager:viale_manager_reservation_delete', args=[r.id])
        rows.append([
            _id_cell(r.id, public_url),
            r.remarques_accueil or '—',
            _toggle_cell(toggle_url, csrf, r.link_sent),
            _bool_label(bool(r.confirmed_at), 'Confirmée', 'En attente'),
            _check_cross(r.groupe),
            _actions_cell(public_url, edit_url, delete_url, csrf),
        ])

    return {
        'reservation_widget': {
            'table': {
                'headers': ['Id', 'Remarques accueil', 'Lien envoyé', 'Réservation', 'Groupe', ''],
                'rows': rows,
            },
            'create_url': reverse('viale_manager:viale_manager_reservation_create_link'),
            'create_form': ReservationLinkForm(initial={'max_days_change': 2, 'max_visitors': 10}),
        }
    }