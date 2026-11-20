"""Reglas de permisos por rol. Se aplican en los casos de uso, no solo en las vistas."""
from __future__ import annotations

from .entidades import Contrato, Rol, Usuario
from .excepciones import PermisoDenegado


def puede_ver_todos_los_contratos(u: Usuario) -> bool:
    return u.rol in (Rol.FUNCIONARIO, Rol.AUTORIDAD, Rol.ADMINISTRADOR)


def puede_ver_contrato(u: Usuario, c: Contrato) -> bool:
    if puede_ver_todos_los_contratos(u):
        return True
    return u.rol == Rol.RESPONSABLE and c.id_responsable == u.id


def puede_editar_contratos(u: Usuario) -> bool:
    return u.rol in (Rol.FUNCIONARIO, Rol.ADMINISTRADOR)


def puede_registrar_seguimiento(u: Usuario, c: Contrato) -> bool:
    if u.rol in (Rol.FUNCIONARIO, Rol.ADMINISTRADOR):
        return True
    return u.rol == Rol.RESPONSABLE and c.id_responsable == u.id


def puede_subir_documento(u: Usuario, c: Contrato) -> bool:
    return puede_registrar_seguimiento(u, c)


def puede_ver_reportes(u: Usuario) -> bool:
    return u.rol in (Rol.FUNCIONARIO, Rol.AUTORIDAD, Rol.ADMINISTRADOR)


def es_administrador(u: Usuario) -> bool:
    return u.rol == Rol.ADMINISTRADOR


def exigir(condicion: bool, mensaje: str = "No tiene permiso para realizar esta operación.") -> None:
    if not condicion:
        raise PermisoDenegado(mensaje)
