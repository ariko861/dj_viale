from django.urls import path
from unfold.sites import UnfoldAdminSite


class VialeAdminSite(UnfoldAdminSite):
    site_title = 'Viale Manager'
    site_header = 'Viale — Gestion des séjours'
    index_title = 'Tableau de bord'
    settings_name = 'UNFOLD_VIALE'

    def get_urls(self):
        from viale_manager.views.calendrier import (
            CalendrierView, CalendrierResourcesView, CalendrierEventsView
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
        ]
        return custom + super().get_urls()


viale_admin = VialeAdminSite(name='viale_manager')
