from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import escapejs, format_html
from django.utils.safestring import mark_safe
from unfold.widgets import UnfoldBooleanSwitchWidget

from viale_manager.forms import ReservationLinkForm
from viale_manager.models import Reservations


def _label(text, variant, icon=None, title=None):
    """Badge coloré Unfold (helper label.html)."""
    return render_to_string('unfold/helpers/label.html', {
        'text': text, 'variant': variant, 'icon': icon, 'label_title': title,
    })


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


def _statut_label(r):
    if r.confirmed_at:
        return _label('Confirmée', 'success', icon='check')
    if r.lien_expire:
        return _label('Lien expiré', 'warning', icon='schedule', title="Renvoyer le lien pour le réactiver.")
    return _label('En attente', 'danger', icon='close')


def _check_cross(value):
    if value:
        return mark_safe('<span class="material-symbols-outlined text-green-600">check</span>')
    return mark_safe('<span class="material-symbols-outlined text-red-500">close</span>')


def _post_button(url, csrf, icon, title, confirm_msg, hover='hover:text-primary-600'):
    return format_html(
        '<form method="post" action="{}" class="inline" onsubmit="return confirm(\'{}\');">'
        '<input type="hidden" name="csrfmiddlewaretoken" value="{}">'
        '<button type="submit" title="{}" '
        'class="material-symbols-outlined text-base-400 {} cursor-pointer">{}</button>'
        '</form>',
        url, escapejs(confirm_msg), csrf, title, hover, icon,
    )


def _actions_cell(r, public_url, csrf, peut):
    parts = [format_html(
        '<a href="{}" target="_blank" title="Ouvrir le formulaire" '
        'class="material-symbols-outlined text-base-400 hover:text-primary-600">open_in_new</a>',
        public_url,
    )]
    if r.contact_email and peut['change']:
        parts.append(_post_button(
            reverse('viale_manager:viale_manager_reservation_send_link', args=[r.id]), csrf,
            'send', 'Envoyer le lien par email',
            f'Envoyer le lien de réservation à {r.contact_email} ?',
        ))
    if peut['change']:
        parts.append(format_html(
            '<a href="{}" title="Modifier les paramètres" '
            'class="material-symbols-outlined text-base-400 hover:text-primary-600">edit</a>',
            reverse('viale_manager:viale_manager_reservations_change', args=[r.id]),
        ))
    # Une réservation confirmée ou dont le lien est parti ne se supprime pas d'ici.
    if not r.confirmed_at and not r.link_sent and peut['delete']:
        parts.append(_post_button(
            reverse('viale_manager:viale_manager_reservation_delete', args=[r.id]), csrf,
            'delete', 'Supprimer', 'Supprimer cette réservation et ses séjours ?',
            hover='hover:text-red-500',
        ))
    return format_html(
        '<div class="flex items-center gap-1 justify-end">{}</div>',
        mark_safe(''.join(parts)),
    )


def reservations_widget_context(request, limit=8):
    """Contexte du widget de gestion des liens de réservation.

    Construit un dict ``table`` consommé par le composant Unfold
    ``unfold/components/table.html``. Réutilisé dans l'index admin et
    au-dessus de la liste des séjours. Vide sans la permission de voir les
    réservations (les liens copiables donnent accès aux formulaires) ; les
    boutons suivent les permissions d'ajout, de modification et de suppression.
    """
    peut = {a: request.user.has_perm(f'viale_manager.{a}_reservations') for a in ('view', 'add', 'change', 'delete')}
    if not peut['view']:
        return {}
    csrf = get_token(request)
    rows = []
    for r in Reservations.objects.order_by('-id')[:limit]:
        public_url = request.build_absolute_uri(reverse('reservation_form', args=[r.link_token]))
        toggle_url = reverse('viale_manager:viale_manager_reservation_toggle_link_sent', args=[r.id])
        rows.append([
            _id_cell(r.id, public_url),
            r.remarques_accueil or '—',
            _toggle_cell(toggle_url, csrf, r.link_sent) if peut['change'] else _check_cross(r.link_sent),
            _statut_label(r),
            _check_cross(r.groupe),
            _actions_cell(r, public_url, csrf, peut),
        ])

    return {
        'reservation_widget': {
            'table': {
                'headers': ['Id', 'Remarques accueil', 'Lien envoyé', 'Réservation', 'Groupe', ''],
                'rows': rows,
            },
            'create_url': reverse('viale_manager:viale_manager_reservation_create_link'),
            'add_url': reverse('viale_manager:viale_manager_reservations_add'),
            'create_form': ReservationLinkForm(initial={'max_days_change': 2, 'max_visitors': 10}),
            'peut_ajouter': peut['add'],
        }
    }