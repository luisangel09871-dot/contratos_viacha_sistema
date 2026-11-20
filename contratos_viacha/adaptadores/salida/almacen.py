"""Adaptador AlmacenDocumentos: carpeta local. Solo acepta nombres generados por el sistema
(uuid + extensión permitida) y comprueba que la ruta final no salga de la carpeta."""
from __future__ import annotations

import re
from pathlib import Path

from ...aplicacion.puertos.salida import AlmacenDocumentos

_NOMBRE_VALIDO = re.compile(r"^[0-9a-f]{32}\.(pdf|docx|txt)$")


class AlmacenLocal(AlmacenDocumentos):
    def __init__(self, carpeta: Path):
        self.carpeta = Path(carpeta)
        self.carpeta.mkdir(parents=True, exist_ok=True)

    def _ruta(self, nombre_archivo: str) -> Path:
        if not _NOMBRE_VALIDO.match(nombre_archivo):
            raise ValueError("Nombre de archivo no válido")
        ruta = (self.carpeta / nombre_archivo).resolve()
        if self.carpeta.resolve() not in ruta.parents:
            raise ValueError("Ruta fuera del almacén")
        return ruta

    def guardar(self, nombre_archivo: str, contenido: bytes) -> None:
        self._ruta(nombre_archivo).write_bytes(contenido)

    def leer(self, nombre_archivo: str) -> bytes:
        return self._ruta(nombre_archivo).read_bytes()


class AlmacenEnMemoria(AlmacenDocumentos):
    def __init__(self):
        self.archivos: dict[str, bytes] = {}

    def guardar(self, nombre_archivo: str, contenido: bytes) -> None:
        self.archivos[nombre_archivo] = contenido

    def leer(self, nombre_archivo: str) -> bytes:
        return self.archivos[nombre_archivo]
