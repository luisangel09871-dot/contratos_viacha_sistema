"""Verifica la clave y el modelo de Gemini ANTES de la demostración:
    python manage.py probar_gemini
Si falla, el chatbot sigue funcionando con plantillas; este comando solo ayuda a diagnosticar."""
from django.conf import settings
from django.core.management.base import BaseCommand

from contratos_viacha.adaptadores.salida.gemini import AdaptadorGemini
from contratos_viacha.aplicacion.puertos.salida import ErrorModeloLenguaje


class Command(BaseCommand):
    help = "Prueba la conexión con la API de Gemini usando GEMINI_API_KEY y GEMINI_MODELO."

    def handle(self, *args, **o):
        if not settings.GEMINI_API_KEY:
            self.stdout.write(self.style.WARNING("GEMINI_API_KEY no está definida en .env: el chatbot usará plantillas."))
            return
        self.stdout.write(f"Modelo: {settings.GEMINI_MODELO}")
        try:
            r = AdaptadorGemini(settings.GEMINI_API_KEY, settings.GEMINI_MODELO, settings.GEMINI_TIMEOUT).generar(
                "Responde en una frase corta.", "Di exactamente: conexión correcta")
            self.stdout.write(self.style.SUCCESS(f"Gemini respondió: {r}"))
        except ErrorModeloLenguaje as e:
            self.stdout.write(self.style.ERROR(f"No funcionó: {e}"))
            self.stdout.write("Revise la clave, el nombre del modelo (GEMINI_MODELO, tómelo de Google AI Studio) y su cuota.")
