from django.urls import path

from core.views import document_reunion, procuration_document, reunion_document, reunion_ical

urlpatterns = [
    path('reunions/<int:pk>/ical/', reunion_ical, name='reunion-ical'),
    path('reunions/<int:reunion_pk>/documents/<int:modele_pk>/', reunion_document, name='reunion-document'),
    path('documents/<uuid:token>/', document_reunion, name='document-reunion'),
    path('procurations/<int:pk>/', procuration_document, name='procuration-document'),
]