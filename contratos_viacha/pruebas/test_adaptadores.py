"""Pruebas de los ADAPTADORES de salida que no necesitan base de datos."""
import io
import json
import urllib.error

import pytest

from contratos_viacha.adaptadores.salida import gemini as g
from contratos_viacha.adaptadores.salida.almacen import AlmacenLocal
from contratos_viacha.adaptadores.salida.extractor import ExtractorArchivos
from contratos_viacha.aplicacion.puertos.salida import ErrorModeloLenguaje


class _Respuesta:
    def __init__(self, datos): self._b = json.dumps(datos).encode()
    def read(self): return self._b
    def __enter__(self): return self
    def __exit__(self, *a): return False


def _gemini(): return g.AdaptadorGemini("clave-de-prueba", "modelo-x", 3)


def test_gemini_arma_la_peticion_y_lee_la_respuesta(monkeypatch):
    visto = {}

    def falso(req, timeout):
        visto.update(url=req.full_url, clave=req.get_header("X-goog-api-key"), cuerpo=json.loads(req.data), timeout=timeout)
        return _Respuesta({"candidates": [{"content": {"parts": [{"text": "Hola "}, {"text": "mundo"}]}}]})
    monkeypatch.setattr(g.urllib.request, "urlopen", falso)
    assert _gemini().generar("instruccion", "contexto") == "Hola mundo"
    assert "modelo-x:generateContent" in visto["url"] and visto["clave"] == "clave-de-prueba"
    assert "clave-de-prueba" not in visto["url"]  # la clave va en la cabecera, nunca en la URL
    assert visto["cuerpo"]["system_instruction"]["parts"][0]["text"] == "instruccion" and visto["timeout"] == 3


@pytest.mark.parametrize("fallo", [
    urllib.error.HTTPError("u", 429, "cuota", {}, io.BytesIO(b"")), urllib.error.URLError("sin red"), TimeoutError(), ValueError("json")])
def test_gemini_traduce_cualquier_falla_a_error_del_puerto(monkeypatch, fallo):
    def falso(req, timeout): raise fallo
    monkeypatch.setattr(g.urllib.request, "urlopen", falso)
    with pytest.raises(ErrorModeloLenguaje):
        _gemini().generar("i", "c")


@pytest.mark.parametrize("datos", [{}, {"candidates": []}, {"candidates": [{"content": {"parts": [{"text": "  "}]}}]}])
def test_gemini_respuesta_vacia_o_inesperada_es_error(monkeypatch, datos):
    monkeypatch.setattr(g.urllib.request, "urlopen", lambda req, timeout: _Respuesta(datos))
    with pytest.raises(ErrorModeloLenguaje):
        _gemini().generar("i", "c")


def test_almacen_rechaza_nombres_que_no_genero_el_sistema(tmp_path):
    a = AlmacenLocal(tmp_path / "docs")
    uid = "a" * 32
    a.guardar(f"{uid}.txt", b"ok")
    assert a.leer(f"{uid}.txt") == b"ok"
    for malo in ("../fuera.txt", "..\\fuera.txt", f"{uid}.exe", f"{uid}.txt/../../x", "/etc/passwd", "nombre.txt", f"{uid}.PDF"):
        with pytest.raises(ValueError):
            a.guardar(malo, b"x")
        with pytest.raises(ValueError):
            a.leer(malo)
    assert [p.name for p in (tmp_path / "docs").iterdir()] == [f"{uid}.txt"]


def test_extractor_txt_con_acentos_y_latin1():
    x = ExtractorArchivos()
    assert x.extraer("txt", "Cláusula séptima".encode("utf-8")) == "Cláusula séptima"
    assert x.extraer("txt", "Cláusula".encode("latin-1")) == "Cláusula"


def test_extractor_docx_lee_parrafos_y_tablas():
    from docx import Document
    d = Document(); d.add_paragraph("Primer párrafo"); t = d.add_table(rows=1, cols=2)
    t.rows[0].cells[0].text, t.rows[0].cells[1].text = "Multa", "5 por ciento"
    b = io.BytesIO(); d.save(b)
    texto = ExtractorArchivos().extraer("docx", b.getvalue())
    assert "Primer párrafo" in texto and "Multa | 5 por ciento" in texto


def test_extractor_pdf_y_errores():
    from pypdf import PdfWriter
    w = PdfWriter(); w.add_blank_page(200, 200); b = io.BytesIO(); w.write(b)
    assert ExtractorArchivos().extraer("pdf", b.getvalue()) == ""  # PDF válido sin texto: no falla
    w2 = PdfWriter(); w2.add_blank_page(200, 200); w2.encrypt("secreto"); b2 = io.BytesIO(); w2.write(b2)
    with pytest.raises(ValueError):
        ExtractorArchivos().extraer("pdf", b2.getvalue())
    with pytest.raises(Exception):
        ExtractorArchivos().extraer("pdf", b"%PDF-1.4 roto")
    with pytest.raises(ValueError):
        ExtractorArchivos().extraer("exe", b"x")
