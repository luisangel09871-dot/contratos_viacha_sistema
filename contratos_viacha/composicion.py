"""Raíz de composición: el ÚNICO lugar donde se conectan casos de uso con adaptadores concretos.
Aquí se decide qué tecnología implementa cada puerto de salida."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from django.conf import settings

from .aplicacion.casos_de_uso.administrar_usuarios import AdministrarUsuariosCU
from .aplicacion.casos_de_uso.consultar_por_chatbot import ConsultarPorChatbotCU
from .aplicacion.casos_de_uso.consultar_vencimientos import ConsultarVencimientosCU
from .aplicacion.casos_de_uso.documentos import ConsultarDocumentosCU, SubirDocumentoCU
from .aplicacion.casos_de_uso.gestionar_contratos import GestionarContratosCU
from .aplicacion.casos_de_uso.registrar_seguimiento import RegistrarSeguimientoCU
from .aplicacion.casos_de_uso.revisar_vencimientos import EjecutarRevisionDiariaCU
from .adaptadores.salida.almacen import AlmacenLocal
from .adaptadores.salida.clasificador import ClasificadorCompuesto, ClasificadorPorReglas
from .adaptadores.salida.correo import NotificadorSMTP
from .adaptadores.salida.extractor import ExtractorArchivos
from .adaptadores.salida.gemini import AdaptadorGemini
from .adaptadores.salida.persistencia import repositorios as r
from .adaptadores.salida.reloj import RelojReal


@dataclass
class Servicios:
    gestionar: GestionarContratosCU
    consultar: ConsultarVencimientosCU
    seguimiento: RegistrarSeguimientoCU
    revision: EjecutarRevisionDiariaCU
    usuarios: AdministrarUsuariosCU
    subir_documento: SubirDocumentoCU
    documentos: ConsultarDocumentosCU
    chatbot: ConsultarPorChatbotCU


_AUTO = object()


def construir(reloj=None, notificador=None, almacen=None, extractor=None, modelo=_AUTO) -> Servicios:
    """Ensambla todos los casos de uso. En pruebas se pueden inyectar reloj, correo, almacén y modelo falsos."""
    reloj = reloj or RelojReal()
    notificador = notificador or NotificadorSMTP()
    almacen = almacen or AlmacenLocal(settings.DOCUMENTOS_DIR)
    extractor = extractor or ExtractorArchivos()
    if modelo is _AUTO:  # sin clave de Gemini, el chatbot responde con plantillas
        modelo = (AdaptadorGemini(settings.GEMINI_API_KEY, settings.GEMINI_MODELO, settings.GEMINI_TIMEOUT)
                  if settings.GEMINI_API_KEY else None)

    contratos, contratistas, tipos = r.RepositorioContratosORM(), r.RepositorioContratistasORM(), r.RepositorioTiposContratoORM()
    garantias, alertas, seguimientos = r.RepositorioGarantiasORM(), r.RepositorioAlertasORM(), r.RepositorioSeguimientosORM()
    usuarios, documentos, umbrales = r.RepositorioUsuariosORM(), r.RepositorioDocumentosORM(), r.RepositorioUmbralesORM()
    consultas, auditoria, tx = r.RepositorioConsultasChatbotORM(), r.RegistroAuditoriaORM(reloj), r.TransaccionORM()

    consultar = ConsultarVencimientosCU(contratos, garantias, alertas, umbrales, reloj)
    docs = ConsultarDocumentosCU(contratos, documentos, almacen, auditoria)
    clasificador = ClasificadorCompuesto(ClasificadorPorReglas(), modelo)
    return Servicios(
        gestionar=GestionarContratosCU(contratos, contratistas, garantias, alertas, seguimientos, documentos,
                                       usuarios, tipos, umbrales, reloj, auditoria, tx),
        consultar=consultar,
        seguimiento=RegistrarSeguimientoCU(contratos, seguimientos, alertas, reloj, auditoria, tx),
        revision=EjecutarRevisionDiariaCU(contratos, garantias, alertas, usuarios, notificador, umbrales, reloj, auditoria),
        usuarios=AdministrarUsuariosCU(usuarios, umbrales, auditoria, tx),
        subir_documento=SubirDocumentoCU(contratos, documentos, almacen, extractor, reloj, auditoria, tx),
        documentos=docs,
        chatbot=ConsultarPorChatbotCU(clasificador, consultar, docs, contratos, seguimientos, umbrales,
                                      consultas, reloj, modelo),
    )


@lru_cache(maxsize=1)
def servicios() -> Servicios:
    return construir()


def reiniciar() -> None:
    servicios.cache_clear()
