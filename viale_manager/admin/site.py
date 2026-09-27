from django.urls import path
from unfold.sites import UnfoldAdminSite


class VialeAdminSite(UnfoldAdminSite):
    site_title = 'Viale Manager'
    site_header = 'Viale — Gestion des séjours'
    index_title = 'Tableau de bord'
    settings_name = 'UNFOLD_VIALE'
    index_template = 'viale_manager/admin/index.html'

    def get_urls(self):
        from viale_manager.views.calendrier import (
            CalendrierView, CalendrierResourcesView, CalendrierEventsView
        )
        from viale_manager.views.reservation_admin import (
            reservation_create_link, reservation_toggle_link_sent, reservation_delete,
            reservation_send_link,
        )
        custom = [
            path(
                'calendrier/',
                self.admin_view(CalendrierView.as_view(admin_site=self)),
                name='viale_manager_calendrier',
            ),
            path(
                'calendrier/resources/',
                self.admin_view(CalendrierResourcesView.as_view()),
                name='viale_manager_calendrier_resources',
            ),
            path(
                'calendrier/events/',
                self.admin_view(CalendrierEventsView.as_view()),
                name='viale_manager_calendrier_events',
            ),
            path(
                'reservations/create-link/',
                self.admin_view(reservation_create_link),
                name='viale_manager_reservation_create_link',
            ),
            path(
                'reservations/<int:pk>/toggle-link-sent/',
                self.admin_view(reservation_toggle_link_sent),
                name='viale_manager_reservation_toggle_link_sent',
            ),
            path(
                'reservations/<int:pk>/send-link/',
                self.admin_view(reservation_send_link),
                name='viale_manager_reservation_send_link',
            ),
            path(
                'reservations/<int:pk>/delete-link/',
                self.admin_view(reservation_delete),
                name='viale_manager_reservation_delete',
            ),
        ]
        return custom + super().get_urls()


viale_admin = VialeAdminSite(name='viale_manager')
