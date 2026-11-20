"""Motor de vencimientos: caso de uso EjecutarRevisionDiaria.

Recorre los contratos activos, recalcula su estado con las reglas determinísticas y
genera las alertas que correspondan. No usa inteligencia artificial.
"""
from __future__ import annotations

from datetime import timedelta

from ...dominio.entidades import Alerta, Contrato, ResultadoRevision
from ...dominio.reglas_vencimiento import dias_restantes, estado_para_contrato, nivel_alerta_pendiente
from ..puertos.entrada import EjecutarRevisionDiaria
from ..puertos.salida import (NotificadorCorreo, RegistroAuditoria, RelojDelSistema, RepositorioAlertas,
                              RepositorioContratos, RepositorioGarantias, RepositorioUmbrales, RepositorioUsuarios)
from ._comun import etiqueta_dias, fmt_fecha


def _mensaje(nivel: str, c: Contrato, dias: int) -> str:
    base = f"Contrato {c.numero} ({c.objeto[:70]}): "
    if nivel == "vencido":
        return base + f"venció el {fmt_fecha(c.fecha_vencimiento)}. Requiere acción inmediata."
    if nivel == "critico":
        return base + f"estado CRÍTICO, {etiqueta_dias(dias)} ({fmt_fecha(c.fecha_vencimiento)})."
    return base + f"{etiqueta_dias(dias)} ({fmt_fecha(c.fecha_vencimiento)}). Evalúe su renovación o cierre."


class EjecutarRevisionDiariaCU(EjecutarRevisionDiaria):
    def __init__(self, contratos: RepositorioContratos, garantias: RepositorioGarantias,
                 alertas: RepositorioAlertas, usuarios: RepositorioUsuarios, notificador: NotificadorCorreo,
                 umbrales: RepositorioUmbrales, reloj: RelojDelSistema, auditoria: RegistroAuditoria):
        self.contratos, self.garantias, self.alertas = contratos, garantias, alertas
        self.usuarios, self.notificador, self.umbrales = usuarios, notificador, umbrales
        self.reloj, self.auditoria = reloj, auditoria

    def _emitir(self, c: Contrato, nivel: str, mensaje: str, res: ResultadoRevision) -> None:
        responsable = self.usuarios.obtener(c.id_responsable)
        enviado = False
        if responsable and responsable.activo and responsable.correo:
            asunto = f"[Contratos GAM Viacha] Alerta: contrato {c.numero}"
            enviado = self.notificador.enviar(responsable.correo, asunto, mensaje)
        self.alertas.guardar(Alerta(None, c.id, nivel, "correo" if enviado else "sistema",
                                    self.reloj.ahora(), False, mensaje, c.numero))
        res.alertas_generadas += 1
        res.correos_enviados += 1 if enviado else 0
        res.detalle.append(f"{c.numero}: {nivel}")

    def ejecutar(self) -> ResultadoRevision:
        hoy, umb = self.reloj.hoy(), self.umbrales.obtener()
        res = ResultadoRevision()
        for c in self.contratos.listar_activos():
            res.contratos_revisados += 1
            nuevo = estado_para_contrato(c.estado, c.fecha_vencimiento, hoy, umb)
            if nuevo != c.estado:
                self.contratos.actualizar_estado(c.id, nuevo)
                res.estados_actualizados += 1
                c.estado = nuevo
            dias = dias_restantes(c.fecha_vencimiento, hoy)
            emitidos = self.alertas.niveles_emitidos(c.id)
            nivel = nivel_alerta_pendiente(nuevo, dias, emitidos, self.alertas.critico_emitido_en(c.id, hoy), umb)
            if nivel:
                self._emitir(c, nivel, _mensaje(nivel, c, dias), res)
            # garantías: una alerta por garantía cuando faltan umbral.aviso_2 días o menos
            for g in self.garantias.listar_por_contrato(c.id):
                gd = dias_restantes(g.fecha_vencimiento, hoy)
                nivel_g = f"garantia_{g.id}"
                if gd <= umb.aviso_2 and nivel_g not in emitidos and gd >= -30:
                    msg = (f"Contrato {c.numero}: la {g.tipo} de garantía {etiqueta_dias(gd)} "
                           f"({fmt_fecha(g.fecha_vencimiento)}).")
                    self._emitir(c, nivel_g, msg, res)
        self.auditoria.registrar(None, "alerta", "REVISION",
                                 f"Revisión del {fmt_fecha(hoy)}: {res.contratos_revisados} contratos, "
                                 f"{res.estados_actualizados} estados actualizados, {res.alertas_generadas} alertas")
        return res
