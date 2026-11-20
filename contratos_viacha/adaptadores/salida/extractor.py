"""Adaptador ExtractorTexto: PDF (pypdf), DOCX (python-docx) y TXT."""
from __future__ import annotations

import io

from ...aplicacion.puertos.salida import ExtractorTexto


class ExtractorArchivos(ExtractorTexto):
    def extraer(self, tipo: str, contenido: bytes) -> str:
        if tipo == "txt":
            for codificacion in ("utf-8", "latin-1"):
                try:
                    return contenido.decode(codificacion)
                except UnicodeDecodeError:
                    continue
        if tipo == "pdf":
            from pypdf import PdfReader
            lector = PdfReader(io.BytesIO(contenido))
            if lector.is_encrypted:
                raise ValueError("PDF protegido con contraseña")
            return "\n".join((pagina.extract_text() or "") for pagina in lector.pages)
        if tipo == "docx":
            from docx import Document
            doc = Document(io.BytesIO(contenido))
            partes = [p.text for p in doc.paragraphs]
            for tabla in doc.tables:
                for fila in tabla.rows:
                    partes.append(" | ".join(c.text for c in fila.cells))
            return "\n".join(partes)
        raise ValueError("Tipo no soportado")


class ExtractorSimulado(ExtractorTexto):
    """Para pruebas sin dependencias: devuelve el contenido como texto."""

    def extraer(self, tipo: str, contenido: bytes) -> str:
        return contenido.decode("utf-8", errors="ignore")
