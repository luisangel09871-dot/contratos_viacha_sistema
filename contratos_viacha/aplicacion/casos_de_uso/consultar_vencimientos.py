"""Casos de uso de consulta: búsqueda, panel con mapa de riesgo y reportes."""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Optional

from ...dominio import permisos
from ...dominio.entidades import Contrato, EstadoContrato, FiltroContratos, Garantia, Rol, Usuario
from ...dominio.excepciones import ErrorValidacion
from ...dominio.reglas_vencimiento import dias_restantes, estado_para_contrato
from ..puertos.entrada import ConsultarVencimientos
from ..puertos.salida import (RelojDelSistema, RepositorioAlertas, RepositorioContratos, RepositorioGarantias,
                              RepositorioUmbrales)


def _restriccion(actor: Usuario) -> Optional[int]:
    """Un responsable solo ve sus contratos; el resto ve todos."""
    return actor.id if actor.rol == Rol.RESPONSABLE else None


class ConsultarVencimientosCU(ConsultarVencimientos):
    def __init__(self, contratos: RepositorioContratos, garantias: RepositorioGarantias,
                 alertas: RepositorioAlertas, umbrales: RepositorioUmbrales, reloj: RelojDelSistema):
        self.contratos, self.garantias, self.alertas = contratos, garantias, alertas
        self.umbrales, self.reloj = umbrales, reloj

    def _con_estado_vigente(self, contratos: list[Contrato]) -> list[Contrato]:
        """Recalcula el estado con la fecha de hoy, para no depender de que el motor ya haya corrido."""
        hoy, umb = self.reloj.hoy(), self.umbrales.obtener()
        for c in contratos:
            c.estado = estado_para_contrato(c.estado, c.fecha_vencimiento, hoy, umb)
        return contratos

    def buscar(self, actor: Usuario, filtro: FiltroContratos) -> list[Contrato]:
        res = self._con_estado_vigente(self.contratos.buscar(filtro, _restriccion(actor)))
        if filtro.estado:  # el estado se filtra ya recalculado
            res = [c for c in res if c.estado.value == filtro.estado]
        return res

    def panel(self, actor: Usuario) -> dict[str, Any]:
        hoy, umb = self.reloj.hoy(), self.umbrales.obtener()
        visibles = self._con_estado_vigente(self.contratos.buscar(FiltroContratos(), _restriccion(actor)))
        conteos = {e.value: 0 for e in EstadoContrato}
        for c in visibles:
            conteos[c.estado.value] += 1
        vigilados = sorted((c for c in visibles if not c.estado.es_final),
                           key=lambda c: c.fecha_vencimiento)
        mapa = [{"contrato": c, "dias": dias_restantes(c.fecha_vencimiento, hoy)} for c in vigilados
                if c.estado != EstadoContrato.VIGENTE]
        gar = self.garantias.por_vencer(hoy, hoy + timedelta(days=umb.dias_proximo), _restriccion(actor))
        return {
            "conteos": conteos, "total": len(visibles),
            "mapa": mapa,
            "urgentes": [m for m in mapa if m["contrato"].estado in (EstadoContrato.CRITICO, EstadoContrato.VENCIDO)][:8],
            "alertas_pendientes": len(self.alertas.listar(_restriccion(actor), solo_no_leidas=True)),
            "garantias_por_vencer": len(gar),
            "umbrales": umb, "hoy": hoy,
        }

    def vencen_en(self, actor: Usuario, dias: int) -> list[Contrato]:
        hoy = self.reloj.hoy()
        filtro = FiltroContratos(vence_desde=hoy, vence_hasta=hoy + timedelta(days=dias))
        res = self._con_estado_vigente(self.contratos.buscar(filtro, _restriccion(actor)))
        return [c for c in res if not c.estado.es_final]

    def vencidos(self, actor: Usuario) -> list[Contrato]:
        hoy = self.reloj.hoy()
        res = self._con_estado_vigente(
            self.contratos.buscar(FiltroContratos(vence_hasta=hoy - timedelta(days=1)), _restriccion(actor)))
        return [c for c in res if c.estado == EstadoContrato.VENCIDO]

    def garantias_por_vencer(self, actor: Usuario, dias: int) -> list[Garantia]:
        hoy = self.reloj.hoy()
        return self.garantias.por_vencer(hoy, hoy + timedelta(days=dias), _restriccion(actor))

    def reporte(self, actor: Usuario, tipo: str) -> list[Contrato]:
        permisos.exigir(permisos.puede_ver_reportes(actor), "No tiene permiso para ver reportes.")
        if tipo == "por_vencer":
            return self.vencen_en(actor, self.umbrales.obtener().dias_proximo)
        if tipo == "vencidos":
            return self.vencidos(actor)
        if tipo == "todos":
            return sorted(self.buscar(actor, FiltroContratos()), key=lambda c: c.fecha_vencimiento)
        raise ErrorValidacion("Tipo de reporte no válido.")
