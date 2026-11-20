from django.urls import include, path

urlpatterns = [path("", include("contratos_viacha.adaptadores.entrada.web.urls"))]
