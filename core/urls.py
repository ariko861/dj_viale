from django.contrib.auth import views as auth_views
from django.urls import path

from core.views import document_reunion, media_protege, reunion_document, reunion_ical

urlpatterns = [
    path('reunions/<int:pk>/ical/', reunion_ical, name='reunion-ical'),
    path('reunions/<int:reunion_pk>/documents/<int:modele_pk>/', reunion_document, name='reunion-document'),
    path('documents/<uuid:token>/', document_reunion, name='document-reunion'),
    path('media/<path:path>', media_protege, name='media-protege'),
    path(
        'mot-de-passe/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'mot-de-passe/termine/',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
]