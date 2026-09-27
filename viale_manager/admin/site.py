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
        from viale_manager.views.maisonnees import (
            MaisonneesView, maisonnees_assign, maisonnees_create, maisonnees_houses, maisonnees_reset,
        )
        from viale_manager.views.statistiques import PresencesView, StatistiquesView
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
                'maisonnees/',
                self.admin_view(MaisonneesView.as_view(admin_site=self)),
                name='viale_manager_maisonnees_index',
            ),
            path(
                'maisonnees/<int:pk>/',
                self.admin_view(MaisonneesView.as_view(admin_site=self)),
                name='viale_manager_maisonnees',
            ),
            path('maisonnees/nouveau/', self.admin_view(maisonnees_create), name='viale_manager_maisonnees_create'),
            path('maisonnees/<int:pk>/maisons/', self.admin_view(maisonnees_houses), name='viale_manager_maisonnees_houses'),
            path('maisonnees/<int:pk>/reset/', self.admin_view(maisonnees_reset), name='viale_manager_maisonnees_reset'),
            path('maisonnees/<int:pk>/assign/', self.admin_view(maisonnees_assign), name='viale_manager_maisonnees_assign'),
            path(
                'statistiques/',
                self.admin_view(StatistiquesView.as_view(admin_site=self)),
                name='viale_manager_statistiques',
            ),
            path(
                'presences/',
                self.admin_view(PresencesView.as_view(admin_site=self)),
                name='viale_manager_presences',
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
