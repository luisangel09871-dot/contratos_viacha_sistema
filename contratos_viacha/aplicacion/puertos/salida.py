"""Puertos de SALIDA: lo que el núcleo necesita del exterior.

El dominio y los casos de uso solo conocen estas interfaces. Las implementaciones
(PostgreSQL, SMTP, Gemini, carpeta local...) viven en adaptadores/salida.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional

from ...dominio.entidades import (Alerta, ConsultaChatbot, Contratista, Contrato, Documento, EstadoContrato,
                                  FiltroContratos, Garantia, RegistroAuditoriaEntidad, Seguimiento, Umbrales,
                                  Usuario)


class Transaccion(ABC):
    """Unidad de trabajo: las operaciones dentro del bloque se confirman juntas o no se confirman."""

    @abstractmethod
    def atomico(self):
        """Devuelve un administrador de contexto (with ...)."""


class RelojDelSistema(ABC):
    @abstractmethod
    def hoy(self) -> date: ...

    @abstractmethod
    def ahora(self) -> datetime: ...

    @abstractmethod
    def fecha_local(self, momento: datetime) -> date:
        """Fecha (en la zona horaria de la institución) de un instante guardado."""


class RepositorioContratos(ABC):
    @abstractmethod
    def guardar(self, contrato: Contrato) -> Contrato: ...

    @abstractmethod
    def obtener(self, id_contrato: int) -> Optional[Contrato]: ...

    @abstractmethod
    def obtener_por_numero(self, numero: str) -> Optional[Contrato]: ...

    @abstractmethod
    def buscar(self, filtro: FiltroContratos, id_responsable: Optional[int] = None) -> list[Contrato]: ...

    @abstractmethod
    def listar_activos(self) -> list[Contrato]:
        """Contratos que el motor debe vigilar (no renovados ni terminados)."""

    @abstractmethod
    def actualizar_estado(self, id_contrato: int, estado: EstadoContrato) -> None: ...



class RepositorioContratistas(ABC):
    @abstractmethod
    def guardar(self, contratista: Contratista) -> Contratista: ...

    @abstractmethod
    def obtener(self, id_contratista: int) -> Optional[Contratista]: ...

    @abstractmethod
    def obtener_por_nit(self, nit: str) -> Optional[Contratista]: ...

    @abstractmethod
    def listar(self) -> list[Contratista]: ...


class RepositorioTiposContrato(ABC):
    @abstractmethod
    def listar(self) -> list[tuple[int, str]]: ...


class RepositorioGarantias(ABC):
    @abstractmethod
    def guardar(self, garantia: Garantia) -> Garantia: ...

    @abstractmethod
    def listar_por_contrato(self, id_contrato: int) -> list[Garantia]: ...

    @abstractmethod
    def por_vencer(self, desde: date, hasta: date, id_responsable: Optional[int] = None) -> list[Garantia]: ...


class RepositorioAlertas(ABC):
    @abstractmethod
    def guardar(self, alerta: Alerta) -> Alerta: ...

    @abstractmethod
    def niveles_emitidos(self, id_contrato: int) -> set[str]: ...

    @abstractmethod
    def critico_emitido_en(self, id_contrato: int, dia: date) -> bool: ...

    @abstractmethod
    def listar(self, id_responsable: Optional[int] = None, solo_no_leidas: bool = False,
               limite: int = 200) -> list[Alerta]: ...

    @abstractmethod
    def listar_por_contrato(self, id_contrato: int) -> list[Alerta]: ...

    @abstractmethod
    def marcar_leida(self, id_alerta: int) -> None: ...

    @abstractmethod
    def obtener(self, id_alerta: int) -> Optional[Alerta]: ...


class RepositorioSeguimientos(ABC):
    @abstractmethod
    def guardar(self, seguimiento: Seguimiento) -> Seguimiento: ...

    @abstractmethod
    def listar_por_contrato(self, id_contrato: int) -> list[Seguimiento]: ...


class RepositorioUsuarios(ABC):
    @abstractmethod
    def obtener(self, id_usuario: int) -> Optional[Usuario]: ...

    @abstractmethod
    def por_correo(self, correo: str) -> Optional[Usuario]: ...

    @abstractmethod
    def listar(self) -> list[Usuario]: ...

    @abstractmethod
    def crear(self, usuario: Usuario, password: str) -> Usuario: ...

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def cambiar_password(self, id_usuario: int, password: str) -> None: ...

    @abstractmethod
    def verificar_credenciales(self, correo: str, password: str) -> Optional[Usuario]: ...


class RepositorioDocumentos(ABC):
    @abstractmethod
    def guardar(self, documento: Documento) -> Documento: ...

    @abstractmethod
    def obtener(self, id_documento: int) -> Optional[Documento]: ...

    @abstractmethod
    def listar_por_contrato(self, id_contrato: int) -> list[Documento]: ...

    @abstractmethod
    def listar_accesibles(self, id_responsable: Optional[int] = None) -> list[Documento]:
        """Documentos (con su texto) de los contratos visibles. id_responsable=None: todos."""


class RepositorioUmbrales(ABC):
    @abstractmethod
    def obtener(self) -> Umbrales: ...

    @abstractmethod
    def guardar(self, umbrales: Umbrales) -> None: ...


class RepositorioConsultasChatbot(ABC):
    @abstractmethod
    def guardar(self, consulta: ConsultaChatbot) -> None: ...


class RegistroAuditoria(ABC):
    @abstractmethod
    def registrar(self, id_usuario: Optional[int], tabla: str, operacion: str, detalle: str = "") -> None: ...

    @abstractmethod
    def listar(self, limite: int = 200) -> list[RegistroAuditoriaEntidad]: ...


class NotificadorCorreo(ABC):
    @abstractmethod
    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> bool:
        """Devuelve True si el mensaje salió."""


class AlmacenDocumentos(ABC):
    @abstractmethod
    def guardar(self, nombre_archivo: str, contenido: bytes) -> None: ...

    @abstractmethod
    def leer(self, nombre_archivo: str) -> bytes: ...


class ExtractorTexto(ABC):
    @abstractmethod
    def extraer(self, tipo: str, contenido: bytes) -> str: ...


class ErrorModeloLenguaje(Exception):
    """El modelo de lenguaje falló, no respondió a tiempo o superó su cuota."""


class ModeloDeLenguaje(ABC):
    nombre: str = "modelo"

    @abstractmethod
    def generar(self, instruccion: str, contexto: str) -> str:
        """Redacta una respuesta usando SOLO el contexto entregado.
        Debe lanzar ErrorModeloLenguaje si no puede responder."""


class ClasificadorIntenciones(ABC):
    @abstractmethod
    def clasificar(self, texto: str) -> tuple[str, float]:
        """Devuelve (intencion, confianza entre 0 y 1). intencion='desconocida' si no reconoce."""
