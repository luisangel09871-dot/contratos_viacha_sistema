"""Adaptador ModeloDeLenguaje: API de Gemini (Google AI Studio) por HTTPS, sin librerías externas.
La clave se lee del entorno (GEMINI_API_KEY); nunca va en el código."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from ...aplicacion.puertos.salida import ErrorModeloLenguaje, ModeloDeLenguaje

_URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"


class AdaptadorGemini(ModeloDeLenguaje):
    def __init__(self, api_key: str, modelo: str, timeout: float = 8.0):
        self.api_key, self.modelo, self.timeout = api_key, modelo, timeout
        self.nombre = f"gemini:{modelo}"

    def generar(self, instruccion: str, contexto: str) -> str:
        cuerpo = {
            "system_instruction": {"parts": [{"text": instruccion}]},
            "contents": [{"role": "user", "parts": [{"text": contexto}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
        }
        req = urllib.request.Request(_URL.format(modelo=self.modelo), data=json.dumps(cuerpo).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                datos = json.loads(r.read().decode("utf-8"))
            partes = datos["candidates"][0]["content"]["parts"]
            texto = "".join(p.get("text", "") for p in partes).strip()
        except urllib.error.HTTPError as e:
            raise ErrorModeloLenguaje(f"Gemini respondió HTTP {e.code}") from e
        except Exception as e:  # red, tiempo de espera, respuesta inesperada
            raise ErrorModeloLenguaje(f"Gemini no disponible: {type(e).__name__}") from e
        if not texto:
            raise ErrorModeloLenguaje("Gemini devolvió una respuesta vacía")
        return texto


class ModeloFalso(ModeloDeLenguaje):
    """Para pruebas: devuelve un texto fijo, o falla a propósito."""

    def __init__(self, respuesta: str = "respuesta del modelo", falla: bool = False):
        self.respuesta, self.falla, self.nombre = respuesta, falla, "modelo-falso"
        self.llamadas = []

    def generar(self, instruccion: str, contexto: str) -> str:
        self.llamadas.append((instruccion, contexto))
        if self.falla:
            raise ErrorModeloLenguaje("falla simulada")
        return self.respuesta
