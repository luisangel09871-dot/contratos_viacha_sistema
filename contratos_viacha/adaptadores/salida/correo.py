"""Adaptador NotificadorCorreo: SMTP mediante el sistema de correo de Django.
Sin configuración SMTP, el mensaje se imprime en la consola del servidor (modo demostración)."""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

from ...aplicacion.puertos.salida import NotificadorCorreo

log = logging.getLogger(__name__)


class NotificadorSMTP(NotificadorCorreo):
    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> bool:
        try:
            return send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [destinatario], fail_silently=False) > 0
        except Exception as e:  # una caída del correo no debe detener la revisión diaria
            log.warning("No se pudo enviar el correo a %s: %s", destinatario, e)
            return False


class NotificadorSimulado(NotificadorCorreo):
    """Para pruebas: guarda los mensajes en memoria en lugar de enviarlos."""

    def __init__(self, funciona: bool = True):
        self.enviados, self.funciona = [], funciona

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> bool:
        if self.funciona:
            self.enviados.append((destinatario, asunto, cuerpo))
        return self.funciona
