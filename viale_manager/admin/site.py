from unfold.sites import UnfoldAdminSite


class VialeAdminSite(UnfoldAdminSite):
    site_title = 'Viale Manager'
    site_header = 'Viale — Gestion des séjours'
    index_title = 'Tableau de bord'
    settings_name = 'UNFOLD_VIALE'


viale_admin = VialeAdminSite(name='viale_manager')
