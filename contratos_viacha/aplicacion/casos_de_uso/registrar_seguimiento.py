"""Casos de uso: seguimiento de acciones y bandeja de alertas."""
from __future__ import annotations

from ...dominio import permisos
from ...dominio.entidades import Alerta, Rol, Seguimiento, Usuario
from ...dominio.excepciones import NoEncontrado
from ..puertos.entrada import RegistrarSeguimiento
from ..puertos.salida import (RegistroAuditoria, RelojDelSistema, RepositorioAlertas, RepositorioContratos,
                              RepositorioSeguimientos, Transaccion)


class RegistrarSeguimientoCU(RegistrarSeguimiento):
    def __init__(self, contratos: RepositorioContratos, seguimientos: RepositorioSeguimientos,
                 repo_alertas: RepositorioAlertas, reloj: RelojDelSistema, auditoria: RegistroAuditoria,
                 transaccion: Transaccion):
        self.contratos, self.seguimientos, self.repo_alertas = contratos, seguimientos, repo_alertas
        self.reloj, self.auditoria, self.transaccion = reloj, auditoria, transaccion

    def registrar(self, actor: Usuario, id_contrato: int, accion: str):
        contrato = self.contratos.obtener(id_contrato)
        if contrato is None:
            raise NoEncontrado("El contrato no existe.")
        permisos.exigir(permisos.puede_registrar_seguimiento(actor, contrato),
                        "No tiene permiso para registrar seguimiento en este contrato.")
        seg = Seguimiento(None, id_contrato, actor.id, (accion or "").strip(), self.reloj.ahora())
        with self.transaccion.atomico():
            guardado = self.seguimientos.guardar(seg)
            self.auditoria.registrar(actor.id, "seguimiento", "INSERT", f"Seguimiento en contrato {contrato.numero}")
        return guardado

    def alertas(self, actor: Usuario, solo_no_leidas: bool = False) -> list[Alerta]:
        return self.repo_alertas.listar(actor.id if actor.rol == Rol.RESPONSABLE else None, solo_no_leidas)

    def marcar_alerta_leida(self, actor: Usuario, id_alerta: int) -> None:
        alerta = self.repo_alertas.obtener(id_alerta)
        if alerta is None:
            raise NoEncontrado("La alerta no existe.")
        contrato = self.contratos.obtener(alerta.id_contrato)
        permisos.exigir(contrato is not None and permisos.puede_ver_contrato(actor, contrato),
                        "No tiene acceso a esta alerta.")
        self.repo_alertas.marcar_leida(id_alerta)
