from django.urls import path

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
]