"""Adaptadores del puerto RelojDelSistema: reloj real (producción) y reloj falso (pruebas)."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from django.utils import timezone

from ...aplicacion.puertos.salida import RelojDelSistema


class RelojReal(RelojDelSistema):
    def hoy(self) -> date:
        return timezone.localdate()

    def ahora(self) -> datetime:
        return timezone.now()

    def fecha_local(self, momento: datetime) -> date:
        return timezone.localtime(momento).date() if timezone.is_aware(momento) else momento.date()


class RelojFalso(RelojDelSistema):
    """Fecha controlada por la prueba. No usa el reloj del sistema operativo."""

    def __init__(self, hoy: date, hora: int = 9):
        self._hoy, self._hora = hoy, hora

    def hoy(self) -> date:
        return self._hoy

    def ahora(self) -> datetime:
        base = datetime(self._hoy.year, self._hoy.month, self._hoy.day, self._hora, 0, 0)
        return timezone.make_aware(base) if timezone.is_naive(base) else base

    def fecha_local(self, momento: datetime) -> date:
        return timezone.localtime(momento).date() if timezone.is_aware(momento) else momento.date()

    def avanzar(self, dias: int) -> None:
        self._hoy = self._hoy + timedelta(days=dias)
