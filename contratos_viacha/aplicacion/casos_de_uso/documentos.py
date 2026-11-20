"""Casos de uso: subir documentos a un contrato y consultarlos.

Un documento HEREDA el permiso de su contrato: quien no puede ver el contrato,
tampoco puede ver, descargar ni buscar en sus documentos.
"""
from __future__ import annotations

import io
import re
import uuid
import zipfile
from typing import Optional

from ...dominio import permisos
from ...dominio.entidades import Documento, Rol, Usuario
from ...dominio.excepciones import ErrorValidacion, NoEncontrado
from ..puertos.entrada import ConsultarDocumentos, SubirDocumento
from ..puertos.salida import (AlmacenDocumentos, ExtractorTexto, RegistroAuditoria, RelojDelSistema,
                              RepositorioContratos, RepositorioDocumentos, Transaccion)
from ._comun import normalizar

EXTENSIONES_PERMITIDAS = ("pdf", "docx", "txt")
TAMANO_MAXIMO = 10 * 1024 * 1024  # 10 MB
MAX_TEXTO = 300_000


def _nombre_seguro(nombre: str) -> str:
    base = re.split(r"[\\/]", nombre or "")[-1].strip()
    base = re.sub(r"[\x00-\x1f]", "", base)
    return base[:150] or "documento"


def validar_archivo(nombre: str, contenido: bytes) -> str:
    """Valida extensión, tamaño y contenido real. Devuelve la extensión."""
    ext = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
    if ext not in EXTENSIONES_PERMITIDAS:
        raise ErrorValidacion("Tipo de archivo no permitido. Solo se aceptan PDF, DOCX y TXT.")
    if not contenido:
        raise ErrorValidacion("El archivo está vacío.")
    if len(contenido) > TAMANO_MAXIMO:
        raise ErrorValidacion("El archivo supera el tamaño máximo de 10 MB.")
    if ext == "pdf" and not contenido.startswith(b"%PDF"):
        raise ErrorValidacion("El archivo no es un PDF válido.")
    if ext == "docx":
        try:
            with zipfile.ZipFile(io.BytesIO(contenido)) as z:
                if "word/document.xml" not in z.namelist():
                    raise ValueError
        except Exception:
            raise ErrorValidacion("El archivo no es un documento DOCX válido.")
    if ext == "txt":
        if b"\x00" in contenido:
            raise ErrorValidacion("El archivo de texto no es válido.")
    return ext


class SubirDocumentoCU(SubirDocumento):
    def __init__(self, contratos: RepositorioContratos, documentos: RepositorioDocumentos,
                 almacen: AlmacenDocumentos, extractor: ExtractorTexto, reloj: RelojDelSistema,
                 auditoria: RegistroAuditoria, transaccion: Transaccion):
        self.contratos, self.documentos, self.almacen, self.extractor = contratos, documentos, almacen, extractor
        self.reloj, self.auditoria, self.transaccion = reloj, auditoria, transaccion

    def subir(self, actor: Usuario, id_contrato: int, nombre_original: str, contenido: bytes) -> Documento:
        contrato = self.contratos.obtener(id_contrato)
        if contrato is None:
            raise NoEncontrado("El contrato no existe.")
        permisos.exigir(permisos.puede_subir_documento(actor, contrato),
                        "No tiene permiso para subir documentos a este contrato.")
        nombre = _nombre_seguro(nombre_original)
        ext = validar_archivo(nombre, contenido)
        try:
            texto = self.extractor.extraer(ext, contenido)[:MAX_TEXTO]
        except Exception:
            raise ErrorValidacion("No se pudo leer el contenido del archivo. Verifique que no esté dañado.")
        nombre_archivo = f"{uuid.uuid4().hex}.{ext}"  # nunca se usa el nombre original en disco
        doc = Documento(None, id_contrato, nombre, nombre_archivo, ext, len(contenido), actor.id,
                        self.reloj.ahora(), texto, contrato.numero)
        with self.transaccion.atomico():
            self.almacen.guardar(nombre_archivo, contenido)
            guardado = self.documentos.guardar(doc)
            self.auditoria.registrar(actor.id, "documento", "INSERT",
                                     f"Documento «{nombre}» en contrato {contrato.numero}")
        return guardado


_PARADAS = set("de la el los las un una unos unas y o u a en por para con sin sobre del al que se es son lo le "
               "su sus mi me te como cual cuales cuando donde quien quienes hay dice dicen documento documentos "
               "contrato contratos clausula clausulas segun".split())


def _raiz(palabra: str) -> str:
    """Quita el plural más común del español para que «multas» encuentre «multa»."""
    if len(palabra) > 4 and palabra.endswith("es"):
        return palabra[:-2]
    if len(palabra) > 3 and palabra.endswith("s"):
        return palabra[:-1]
    return palabra


def palabras_clave(consulta: str) -> list[str]:
    sin_numero = re.sub(r"\b\d{1,4}\s*/\s*\d{4}\b", " ", consulta or "")  # el número de contrato no es un tema
    return [_raiz(p) for p in re.findall(r"[a-z0-9]{3,}", normalizar(sin_numero)) if p not in _PARADAS]


def _trozos(texto: str, tam: int = 260) -> list[str]:
    """Parte el texto en fragmentos por párrafos, agrupando hasta ~tam caracteres."""
    partes, actual = [], ""
    for linea in re.split(r"\n+", texto):
        linea = linea.strip()
        if not linea:
            continue
        if len(actual) + len(linea) > tam and actual:
            partes.append(actual)
            actual = linea
        else:
            actual = f"{actual} {linea}".strip()
    if actual:
        partes.append(actual)
    return partes


class ConsultarDocumentosCU(ConsultarDocumentos):
    def __init__(self, contratos: RepositorioContratos, documentos: RepositorioDocumentos,
                 almacen: AlmacenDocumentos, auditoria: RegistroAuditoria):
        self.contratos, self.documentos, self.almacen, self.auditoria = contratos, documentos, almacen, auditoria

    def _contrato_visible(self, actor: Usuario, id_contrato: int):
        contrato = self.contratos.obtener(id_contrato)
        if contrato is None:
            raise NoEncontrado("El contrato no existe.")
        permisos.exigir(permisos.puede_ver_contrato(actor, contrato), "No tiene acceso a este contrato.")
        return contrato

    def listar(self, actor: Usuario, id_contrato: int) -> list[Documento]:
        self._contrato_visible(actor, id_contrato)
        return self.documentos.listar_por_contrato(id_contrato)

    def descargar(self, actor: Usuario, id_documento: int) -> tuple[Documento, bytes]:
        doc = self.documentos.obtener(id_documento)
        if doc is None:
            raise NoEncontrado("El documento no existe.")
        self._contrato_visible(actor, doc.id_contrato)
        self.auditoria.registrar(actor.id, "documento", "DESCARGA", f"Documento «{doc.nombre_original}»")
        return doc, self.almacen.leer(doc.nombre_archivo)

    def buscar_fragmentos(self, actor: Usuario, consulta: str, id_contrato: Optional[int] = None) -> list[dict]:
        claves = palabras_clave(consulta)
        if not claves:
            return []
        restr = actor.id if actor.rol == Rol.RESPONSABLE else None
        docs = self.documentos.listar_accesibles(restr)  # ya filtrados por permiso del contrato
        if id_contrato is not None:
            docs = [d for d in docs if d.id_contrato == id_contrato]
        hallados = []
        for d in docs:
            for trozo in _trozos(d.texto_extraido):
                palabras = {_raiz(w) for w in re.findall(r"[a-z0-9]+", normalizar(trozo))}
                puntaje = sum(1 for k in claves if k in palabras)
                if puntaje:
                    hallados.append({"documento_id": d.id, "documento": d.nombre_original,
                                     "contrato_numero": d.contrato_numero, "fragmento": trozo,
                                     "puntaje": puntaje})
        hallados.sort(key=lambda h: h["puntaje"], reverse=True)
        return hallados[:3]
