from django.urls import path

from core.views import reunion_ical

urlpatterns = [
    path('reunions/<int:pk>/ical/', reunion_ical, name='reunion-ical'),
]