from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from viale_manager.views import compte
from viale_manager.views.reservation_form import ReservationFormView, visitor_search

urlpatterns = [
    path(
        'reservation/<uuid:token>/',
        ReservationFormView.as_view(),
        name='reservation_form',
    ),
    path(
        'reservation/<uuid:token>/visitors/',
        visitor_search,
        name='reservation_visitor_search',
    ),
    path('compte/', compte.mon_compte, name='compte'),
    path('compte/inscription/', compte.inscription, name='compte_inscription'),
    path('compte/activer/<str:token>/', compte.activer, name='compte_activer'),
    path('compte/connexion/', compte.ConnexionView.as_view(), name='compte_connexion'),
    path(
        'compte/deconnexion/',
        LogoutView.as_view(next_page=reverse_lazy('compte_connexion')),
        name='compte_deconnexion',
    ),
]
