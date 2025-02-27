"""
URL configuration for futmundi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Inclui todas as URLs do app administrativo
    path('', include('administrativo.urls')),
] 

# Adiciona as URLs para servir arquivos de mídia, independente do ambiente
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Para produção, ainda mantém as URLs, embora o servidor web deva ser configurado para servir estes arquivos diretamente
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
