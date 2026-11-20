"""Casos de uso: registrar y editar contratos, contratistas y garantías, y ver la ficha."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from ...dominio import permisos
from ...dominio.entidades import Contratista, Contrato, EstadoContrato, Garantia, Usuario
from ...dominio.excepciones import ErrorValidacion, NoEncontrado
from ...dominio.reglas_vencimiento import dias_restantes, estado_para_contrato
from ..puertos.entrada import GestionarContratos
from ..puertos.salida import (RegistroAuditoria, RelojDelSistema, RepositorioAlertas, RepositorioContratistas,
                              RepositorioContratos, RepositorioDocumentos, RepositorioGarantias,
                              RepositorioSeguimientos, RepositorioTiposContrato, RepositorioUmbrales,
                              RepositorioUsuarios, Transaccion)


def _decimal(valor) -> Decimal:
    try:
        return Decimal(str(valor).replace(",", ".")) if valor not in (None, "") else Decimal("0")
    except InvalidOperation:
        raise ErrorValidacion("El monto no es un número válido.")


class GestionarContratosCU(GestionarContratos):
    def __init__(self, contratos: RepositorioContratos, contratistas: RepositorioContratistas,
                 garantias: RepositorioGarantias, alertas: RepositorioAlertas,
                 seguimientos: RepositorioSeguimientos, documentos: RepositorioDocumentos,
                 usuarios: RepositorioUsuarios, tipos: RepositorioTiposContrato,
                 umbrales: RepositorioUmbrales, reloj: RelojDelSistema, auditoria: RegistroAuditoria,
                 transaccion: Transaccion):
        self.contratos, self.contratistas, self.garantias = contratos, contratistas, garantias
        self.alertas, self.seguimientos, self.documentos = alertas, seguimientos, documentos
        self.usuarios, self.tipos, self.umbrales = usuarios, tipos, umbrales
        self.reloj, self.auditoria, self.transaccion = reloj, auditoria, transaccion

    # ---- contratos ----
    def _construir(self, datos: dict, id_contrato=None, estado=EstadoContrato.REGISTRADO) -> Contrato:
        for campo in ("numero", "objeto", "id_tipo", "id_contratista", "id_responsable",
                      "fecha_inicio", "fecha_vencimiento"):
            if datos.get(campo) in (None, ""):
                raise ErrorValidacion(f"Falta el dato obligatorio: {campo.replace('_', ' ')}.")
        if self.contratistas.obtener(int(datos["id_contratista"])) is None:
            raise ErrorValidacion("El contratista seleccionado no existe.")
        responsable = self.usuarios.obtener(int(datos["id_responsable"]))
        if responsable is None or not responsable.activo:
            raise ErrorValidacion("El responsable seleccionado no existe o está inactivo.")
        return Contrato(id=id_contrato, numero=str(datos["numero"]).strip(), objeto=str(datos["objeto"]).strip(),
                        id_tipo=int(datos["id_tipo"]), id_contratista=int(datos["id_contratista"]),
                        id_responsable=int(datos["id_responsable"]), monto=_decimal(datos.get("monto")),
                        fecha_inicio=datos["fecha_inicio"], fecha_vencimiento=datos["fecha_vencimiento"],
                        estado=estado)

    def registrar_contrato(self, actor: Usuario, datos: dict) -> Contrato:
        permisos.exigir(permisos.puede_editar_contratos(actor), "Solo el funcionario de contrataciones o el administrador pueden registrar contratos.")
        contrato = self._construir(datos)
        if self.contratos.obtener_por_numero(contrato.numero):
            raise ErrorValidacion(f"Ya existe un contrato con el número {contrato.numero}.")
        contrato.estado = estado_para_contrato(EstadoContrato.REGISTRADO, contrato.fecha_vencimiento,
                                               self.reloj.hoy(), self.umbrales.obtener())
        gar_tipo, gar_venc = datos.get("garantia_tipo"), datos.get("garantia_vencimiento")
        with self.transaccion.atomico():
            guardado = self.contratos.guardar(contrato)
            if gar_tipo and gar_venc:
                self.garantias.guardar(Garantia(None, guardado.id, gar_tipo, gar_venc))
            self.auditoria.registrar(actor.id, "contrato", "INSERT", f"Contrato {guardado.numero} registrado")
        return guardado

    def editar_contrato(self, actor: Usuario, id_contrato: int, datos: dict) -> Contrato:
        permisos.exigir(permisos.puede_editar_contratos(actor), "No tiene permiso para editar contratos.")
        actual = self.contratos.obtener(id_contrato)
        if actual is None:
            raise NoEncontrado("El contrato no existe.")
        nuevo = self._construir(datos, id_contrato=id_contrato, estado=actual.estado)
        otro = self.contratos.obtener_por_numero(nuevo.numero)
        if otro and otro.id != id_contrato:
            raise ErrorValidacion(f"Ya existe un contrato con el número {nuevo.numero}.")
        nuevo.estado = estado_para_contrato(actual.estado, nuevo.fecha_vencimiento, self.reloj.hoy(),
                                            self.umbrales.obtener())
        cambios = [c for c in ("numero", "objeto", "id_tipo", "id_contratista", "id_responsable", "monto",
                               "fecha_inicio", "fecha_vencimiento") if getattr(actual, c) != getattr(nuevo, c)]
        with self.transaccion.atomico():
            guardado = self.contratos.guardar(nuevo)
            self.auditoria.registrar(actor.id, "contrato", "UPDATE",
                                     f"Contrato {guardado.numero} editado. Campos: {', '.join(cambios) or 'sin cambios'}")
        return guardado

    def marcar_estado_final(self, actor: Usuario, id_contrato: int, estado: str) -> Contrato:
        permisos.exigir(permisos.puede_editar_contratos(actor), "No tiene permiso para cambiar el estado.")
        contrato = self.contratos.obtener(id_contrato)
        if contrato is None:
            raise NoEncontrado("El contrato no existe.")
        if estado in ("renovado", "terminado"):
            nuevo = EstadoContrato(estado)
        elif estado == "reabrir":
            nuevo = estado_para_contrato(EstadoContrato.REGISTRADO, contrato.fecha_vencimiento,
                                         self.reloj.hoy(), self.umbrales.obtener())
        else:
            raise ErrorValidacion("Estado no permitido.")
        with self.transaccion.atomico():
            self.contratos.actualizar_estado(id_contrato, nuevo)
            self.auditoria.registrar(actor.id, "contrato", "UPDATE",
                                     f"Contrato {contrato.numero}: estado {contrato.estado.value} -> {nuevo.value}")
        contrato.estado = nuevo
        return contrato

    # ---- contratistas y garantías ----
    def registrar_contratista(self, actor: Usuario, datos: dict) -> Contratista:
        permisos.exigir(permisos.puede_editar_contratos(actor), "No tiene permiso para registrar contratistas.")
        nit = (datos.get("nit") or "").strip() or None
        if nit and self.contratistas.obtener_por_nit(nit):
            raise ErrorValidacion(f"Ya existe un contratista con el NIT {nit}.")
        c = Contratista(None, (datos.get("razon_social") or "").strip(), nit,
                        (datos.get("correo_contacto") or "").strip() or None)
        with self.transaccion.atomico():
            guardado = self.contratistas.guardar(c)
            self.auditoria.registrar(actor.id, "contratista", "INSERT", f"Contratista {guardado.razon_social}")
        return guardado

    def registrar_garantia(self, actor: Usuario, id_contrato: int, tipo: str, vencimiento: date) -> Garantia:
        permisos.exigir(permisos.puede_editar_contratos(actor), "No tiene permiso para registrar garantías.")
        contrato = self.contratos.obtener(id_contrato)
        if contrato is None:
            raise NoEncontrado("El contrato no existe.")
        with self.transaccion.atomico():
            g = self.garantias.guardar(Garantia(None, id_contrato, tipo, vencimiento))
            self.auditoria.registrar(actor.id, "garantia", "INSERT",
                                     f"Garantía ({tipo}) del contrato {contrato.numero}")
        return g

    # ---- consulta ----
    def ficha(self, actor: Usuario, id_contrato: int) -> dict[str, Any]:
        contrato = self.contratos.obtener(id_contrato)
        if contrato is None:
            raise NoEncontrado("El contrato no existe.")
        permisos.exigir(permisos.puede_ver_contrato(actor, contrato), "No tiene acceso a este contrato.")
        hoy = self.reloj.hoy()
        return {
            "contrato": contrato,
            "dias": dias_restantes(contrato.fecha_vencimiento, hoy),
            "garantias": self.garantias.listar_por_contrato(id_contrato),
            "alertas": self.alertas.listar_por_contrato(id_contrato),
            "seguimientos": self.seguimientos.listar_por_contrato(id_contrato),
            "documentos": self.documentos.listar_por_contrato(id_contrato),
            "puede_editar": permisos.puede_editar_contratos(actor),
            "puede_seguimiento": permisos.puede_registrar_seguimiento(actor, contrato),
            "puede_subir": permisos.puede_subir_documento(actor, contrato),
        }

    def catalogos(self, actor: Usuario) -> dict[str, Any]:
        return {"tipos": self.tipos.listar(), "contratistas": self.contratistas.listar(),
                "responsables": [u for u in self.usuarios.listar() if u.activo]}
