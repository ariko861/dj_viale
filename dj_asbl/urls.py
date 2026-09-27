"""
URL configuration for dj_asbl project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from viale_manager.admin import viale_admin
from viale_manager.views.accueil import accueil

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hijack/', include('hijack.urls')),
    path('accueil/', viale_admin.urls),
    path('viale/', include('viale_manager.urls')),
    path('', accueil, name='home'),
    # Liens de l'ancien viale-manager (Laravel), si son domaine pointe ici.
    re_path(
        r'^(?:confirmation|confirmed)/(?P<token>[0-9a-f-]{36})/?$',
        RedirectView.as_view(pattern_name='reservation_form'),
        name='ancien_lien_reservation',
    ),
    path('', include('core.urls')),
]
