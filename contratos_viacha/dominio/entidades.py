"""Entidades del dominio. Python puro (dataclasses): sin Django, sin base de datos."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from .excepciones import ErrorValidacion


class Rol(str, Enum):
    FUNCIONARIO = "funcionario"      # funcionario de contrataciones
    RESPONSABLE = "responsable"      # responsable de contrato
    AUTORIDAD = "autoridad"          # autoridad o unidad jurídica
    ADMINISTRADOR = "administrador"  # administrador del sistema

    @property
    def etiqueta(self) -> str:
        return {
            "funcionario": "Funcionario de contrataciones",
            "responsable": "Responsable de contrato",
            "autoridad": "Autoridad / unidad jurídica",
            "administrador": "Administrador del sistema",
        }[self.value]


class EstadoContrato(str, Enum):
    REGISTRADO = "registrado"
    VIGENTE = "vigente"
    PROXIMO_A_VENCER = "proximo_a_vencer"
    CRITICO = "critico"
    VENCIDO = "vencido"
    RENOVADO = "renovado"
    TERMINADO = "terminado"

    @property
    def etiqueta(self) -> str:
        return {
            "registrado": "Registrado",
            "vigente": "Vigente",
            "proximo_a_vencer": "Próximo a vencer",
            "critico": "Crítico",
            "vencido": "Vencido",
            "renovado": "Renovado",
            "terminado": "Terminado",
        }[self.value]

    @property
    def es_final(self) -> bool:
        """Estados que fija una persona y que el motor no recalcula."""
        return self in (EstadoContrato.RENOVADO, EstadoContrato.TERMINADO)


@dataclass(frozen=True)
class Umbrales:
    """Umbrales de alerta, configurables por el administrador (días)."""
    dias_proximo: int = 30
    dias_critico: int = 7
    aviso_1: int = 30
    aviso_2: int = 15

    def __post_init__(self):
        if not (self.dias_critico >= 0 and self.dias_proximo > self.dias_critico):
            raise ErrorValidacion("El umbral próximo a vencer debe ser mayor que el crítico, y ambos no negativos.")
        if not (self.aviso_1 > self.aviso_2 > 0):
            raise ErrorValidacion("El primer aviso debe ser mayor que el segundo, y ambos positivos.")


@dataclass
class Usuario:
    id: Optional[int]
    nombre_completo: str
    correo: str
    rol: Rol
    activo: bool = True
    id_unidad: Optional[int] = None


@dataclass
class Contratista:
    id: Optional[int]
    razon_social: str
    nit: Optional[str] = None
    correo_contacto: Optional[str] = None

    def __post_init__(self):
        if not self.razon_social or not self.razon_social.strip():
            raise ErrorValidacion("La razón social del contratista es obligatoria.")


@dataclass
class Contrato:
    id: Optional[int]
    numero: str
    objeto: str
    id_tipo: int
    id_contratista: int
    id_responsable: int
    monto: Decimal
    fecha_inicio: date
    fecha_vencimiento: date
    estado: EstadoContrato = EstadoContrato.REGISTRADO
    tipo_nombre: str = ""
    contratista_nombre: str = ""
    responsable_nombre: str = ""

    def __post_init__(self):
        self.validar()

    def validar(self) -> None:
        if not self.numero or not self.numero.strip():
            raise ErrorValidacion("El número de contrato es obligatorio.")
        if not self.objeto or not self.objeto.strip():
            raise ErrorValidacion("El objeto del contrato es obligatorio.")
        if self.monto is None or Decimal(self.monto) < 0:
            raise ErrorValidacion("El monto no puede ser negativo.")
        if self.fecha_vencimiento < self.fecha_inicio:
            raise ErrorValidacion("La fecha de vencimiento no puede ser anterior a la fecha de inicio.")


@dataclass
class Garantia:
    id: Optional[int]
    id_contrato: int
    tipo: str  # "boleta" o "poliza"
    fecha_vencimiento: date
    contrato_numero: str = ""

    def __post_init__(self):
        if self.tipo not in ("boleta", "poliza"):
            raise ErrorValidacion("El tipo de garantía debe ser «boleta» o «póliza».")


@dataclass
class Alerta:
    id: Optional[int]
    id_contrato: int
    nivel: str   # aviso_30, aviso_15, critico, vencido
    canal: str   # sistema, correo
    fecha_emision: datetime
    leida: bool = False
    mensaje: str = ""
    contrato_numero: str = ""


@dataclass
class Seguimiento:
    id: Optional[int]
    id_contrato: int
    id_usuario: int
    accion: str
    fecha: datetime
    usuario_nombre: str = ""

    def __post_init__(self):
        if not self.accion or not self.accion.strip():
            raise ErrorValidacion("Debe describir la acción realizada.")


@dataclass
class Documento:
    id: Optional[int]
    id_contrato: int
    nombre_original: str
    nombre_archivo: str   # nombre aleatorio con el que se guarda
    tipo: str             # pdf, docx, txt
    tamano: int
    subido_por: int
    fecha: datetime
    texto_extraido: str = ""
    contrato_numero: str = ""
    subido_por_nombre: str = ""


@dataclass
class ConsultaChatbot:
    id: Optional[int]
    id_usuario: int
    mensaje: str
    intencion: str
    respuesta: str
    adaptador: str
    fecha_hora: datetime


@dataclass
class RegistroAuditoriaEntidad:
    id: Optional[int]
    id_usuario: Optional[int]
    tabla: str
    operacion: str
    detalle: str
    fecha_hora: datetime
    usuario_nombre: str = ""


@dataclass
class FiltroContratos:
    estado: Optional[str] = None
    id_tipo: Optional[int] = None
    id_contratista: Optional[int] = None
    id_responsable: Optional[int] = None
    texto: Optional[str] = None
    vence_desde: Optional[date] = None
    vence_hasta: Optional[date] = None


@dataclass
class ResultadoRevision:
    contratos_revisados: int = 0
    estados_actualizados: int = 0
    alertas_generadas: int = 0
    correos_enviados: int = 0
    detalle: list = field(default_factory=list)
