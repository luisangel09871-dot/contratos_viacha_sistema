"""Reglas de vencimiento. Aritmética de fechas con reglas explícitas, sin IA.

La fecha de «hoy» NUNCA se obtiene aquí: siempre se recibe como parámetro
(la entrega el puerto RelojDelSistema), para poder probar con un reloj falso.
"""
from __future__ import annotations

from datetime import date
from typing import Iterable, Optional

from .entidades import EstadoContrato, Umbrales


def dias_restantes(fecha_vencimiento: date, hoy: date) -> int:
    """Días que faltan para el vencimiento (negativo si ya venció)."""
    return (fecha_vencimiento - hoy).days


def calcular_estado(fecha_vencimiento: date, hoy: date, umbrales: Umbrales = Umbrales()) -> EstadoContrato:
    """VIGENTE si falta más que dias_proximo; PROXIMO_A_VENCER hasta dias_proximo;
    CRITICO hasta dias_critico (incluye el día 0); VENCIDO si es menor que 0."""
    d = dias_restantes(fecha_vencimiento, hoy)
    if d < 0:
        return EstadoContrato.VENCIDO
    if d <= umbrales.dias_critico:
        return EstadoContrato.CRITICO
    if d <= umbrales.dias_proximo:
        return EstadoContrato.PROXIMO_A_VENCER
    return EstadoContrato.VIGENTE


def estado_para_contrato(estado_actual: EstadoContrato, fecha_vencimiento: date, hoy: date,
                         umbrales: Umbrales = Umbrales()) -> EstadoContrato:
    """Respeta los estados fijados por una persona (renovado, terminado)."""
    if estado_actual.es_final:
        return estado_actual
    return calcular_estado(fecha_vencimiento, hoy, umbrales)


def nivel_alerta_pendiente(estado: EstadoContrato, dias: int, niveles_ya_emitidos: Iterable[str],
                           critico_emitido_hoy: bool, umbrales: Umbrales = Umbrales()) -> Optional[str]:
    """Decide qué alerta toca emitir (o ninguna). Es idempotente:
    si el motor corre dos veces el mismo día no duplica alertas, y si un día
    no corrió, se pone al día con la más urgente.

    - vencido: una sola vez.
    - crítico: una vez por día.
    - próximo a vencer: aviso_15 (a 15 días o menos) y aviso_30 (a 30 días o menos), una vez cada uno.
    """
    emitidos = set(niveles_ya_emitidos)
    if estado == EstadoContrato.VENCIDO:
        return "vencido" if "vencido" not in emitidos else None
    if estado == EstadoContrato.CRITICO:
        return None if critico_emitido_hoy else "critico"
    if estado == EstadoContrato.PROXIMO_A_VENCER:
        if dias <= umbrales.aviso_2 and "aviso_15" not in emitidos:
            return "aviso_15"
        if dias <= umbrales.aviso_1 and "aviso_30" not in emitidos and "aviso_15" not in emitidos:
            return "aviso_30"
    return None
