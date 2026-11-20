"""Utilidades compartidas por los casos de uso (formatos y normalización de texto)."""
from __future__ import annotations

import re
import unicodedata
from datetime import date
from decimal import Decimal


def fmt_fecha(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def fmt_monto(m) -> str:
    m = Decimal(m)
    texto = f"{m:,.2f}"  # 1,234,567.89
    return "Bs " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def sin_acentos(texto: str) -> str:
    n = unicodedata.normalize("NFD", texto)
    return "".join(c for c in n if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, espacios simples."""
    return re.sub(r"\s+", " ", sin_acentos(texto or "").lower()).strip()


def etiqueta_dias(dias: int) -> str:
    if dias < 0:
        n = abs(dias)
        return f"venció hace {n} día{'s' if n != 1 else ''}"
    if dias == 0:
        return "vence hoy"
    return f"vence en {dias} día{'s' if dias != 1 else ''}"
