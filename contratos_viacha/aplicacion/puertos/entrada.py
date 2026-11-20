"""Puertos de ENTRADA: lo que el sistema ofrece al exterior.

Cada puerto corresponde a un grupo de casos de uso de la capa de aplicación.
Los adaptadores de entrada (vistas web, chatbot, tarea programada) solo llaman estas interfaces.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Optional

from ...dominio.entidades import (Alerta, Contratista, Contrato, Documento, FiltroContratos, Garantia,
                                  ResultadoRevision, Rol, Seguimiento, Umbrales, Usuario)


class GestionarContratos(ABC):
    @abstractmethod
    def registrar_contrato(self, actor: Usuario, datos: dict) -> Contrato: ...

    @abstractmethod
    def editar_contrato(self, actor: Usuario, id_contrato: int, datos: dict) -> Contrato: ...

    @abstractmethod
    def marcar_estado_final(self, actor: Usuario, id_contrato: int, estado: str) -> Contrato: ...

    @abstractmethod
    def registrar_contratista(self, actor: Usuario, datos: dict) -> Contratista: ...

    @abstractmethod
    def registrar_garantia(self, actor: Usuario, id_contrato: int, tipo: str, vencimiento: date) -> Garantia: ...

    @abstractmethod
    def ficha(self, actor: Usuario, id_contrato: int) -> dict[str, Any]: ...

    @abstractmethod
    def catalogos(self, actor: Usuario) -> dict[str, Any]:
        """Tipos de contrato, contratistas y responsables para los formularios."""


class ConsultarVencimientos(ABC):
    @abstractmethod
    def buscar(self, actor: Usuario, filtro: FiltroContratos) -> list[Contrato]: ...

    @abstractmethod
    def panel(self, actor: Usuario) -> dict[str, Any]: ...

    @abstractmethod
    def vencen_en(self, actor: Usuario, dias: int) -> list[Contrato]: ...

    @abstractmethod
    def vencidos(self, actor: Usuario) -> list[Contrato]: ...

    @abstractmethod
    def garantias_por_vencer(self, actor: Usuario, dias: int) -> list[Garantia]: ...

    @abstractmethod
    def reporte(self, actor: Usuario, tipo: str) -> list[Contrato]: ...


class RegistrarSeguimiento(ABC):
    @abstractmethod
    def registrar(self, actor: Usuario, id_contrato: int, accion: str) -> Seguimiento: ...

    @abstractmethod
    def alertas(self, actor: Usuario, solo_no_leidas: bool = False) -> list[Alerta]: ...

    @abstractmethod
    def marcar_alerta_leida(self, actor: Usuario, id_alerta: int) -> None: ...


class EjecutarRevisionDiaria(ABC):
    @abstractmethod
    def ejecutar(self) -> ResultadoRevision: ...


class AdministrarUsuarios(ABC):
    @abstractmethod
    def iniciar_sesion(self, correo: str, password: str) -> Usuario: ...

    @abstractmethod
    def listar_usuarios(self, actor: Usuario) -> list[Usuario]: ...

    @abstractmethod
    def crear_usuario(self, actor: Usuario, nombre: str, correo: str, rol: str, password: str) -> Usuario: ...

    @abstractmethod
    def cambiar_rol(self, actor: Usuario, id_usuario: int, rol: str) -> Usuario: ...

    @abstractmethod
    def activar(self, actor: Usuario, id_usuario: int, activo: bool) -> Usuario: ...

    @abstractmethod
    def obtener_umbrales(self, actor: Usuario) -> Umbrales: ...

    @abstractmethod
    def configurar_umbrales(self, actor: Usuario, umbrales: Umbrales) -> Umbrales: ...

    @abstractmethod
    def bitacora(self, actor: Usuario, limite: int = 200) -> list: ...


class SubirDocumento(ABC):
    @abstractmethod
    def subir(self, actor: Usuario, id_contrato: int, nombre_original: str, contenido: bytes) -> Documento: ...


class ConsultarDocumentos(ABC):
    @abstractmethod
    def listar(self, actor: Usuario, id_contrato: int) -> list[Documento]: ...

    @abstractmethod
    def descargar(self, actor: Usuario, id_documento: int) -> tuple[Documento, bytes]: ...

    @abstractmethod
    def buscar_fragmentos(self, actor: Usuario, consulta: str, id_contrato: Optional[int] = None) -> list[dict]: ...


class ConsultarPorChatbot(ABC):
    @abstractmethod
    def consultar(self, actor: Usuario, mensaje: str) -> dict[str, Any]: ...
