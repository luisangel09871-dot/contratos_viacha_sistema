"""Adaptadores ClasificadorIntenciones: reglas con palabras clave (primero) y, solo si las
reglas no reconocen la intención, el modelo de lenguaje como apoyo."""
from __future__ import annotations

import re
from typing import Optional

from ...aplicacion.casos_de_uso._comun import normalizar
from ...aplicacion.casos_de_uso.consultar_por_chatbot import INTENCIONES, extraer_numero
from ...aplicacion.puertos.salida import ClasificadorIntenciones, ModeloDeLenguaje

# intención -> [(expresión regular sobre texto normalizado, peso)]
_REGLAS = {
    "ayuda": [(r"\bayuda\b", 3), (r"que puedes", 3), (r"que sabes", 3), (r"como funcionas", 3), (r"\bhola\b", 3),
              (r"buen(os|as)", 3), (r"comandos", 2), (r"para que sirves", 3), (r"que haces", 3)],
    "responsable": [(r"quien lleva", 3), (r"quien es el responsable", 3), (r"responsable", 2), (r"encargado", 2),
                    (r"a cargo", 2), (r"quien se encarga", 3)],
    "historial": [(r"historial", 3), (r"que se hizo", 3), (r"acciones", 2), (r"seguimiento", 2),
                  (r"antecedentes", 2), (r"que paso con", 3), (r"ultimas acciones", 3)],
    "garantias_por_vencer": [(r"garantia", 3), (r"boleta", 3), (r"poliza", 3)],
    "contratos_vencidos": [(r"vencid[oa]s?", 3), (r"\bvencio\b", 3), (r"expirad[oa]s?", 3), (r"ya vencieron", 3)],
    "vencimientos_proximos": [(r"\bvence\b", 2), (r"\bvencen\b", 2), (r"vencimiento", 2), (r"por vencer", 3),
                              (r"proximos a vencer", 3), (r"\bexpira", 2), (r"a vencer", 2)],
    "consultar_documento": [(r"que dice", 3), (r"clausula", 3), (r"\bmultas?\b", 2), (r"penalidad", 3),
                            (r"documento", 2), (r"archivo", 2), (r"adjunto", 2), (r"\bpdf\b", 2),
                            (r"segun el contrato", 3), (r"dice el", 2)],
    "estado_contrato": [(r"\bestado\b", 2), (r"como esta", 3), (r"como va", 3), (r"situacion", 2),
                        (r"informacion (del|de el) contrato", 3), (r"datos (del|de el) contrato", 3),
                        (r"detalle", 2), (r"cuando vence el contrato", 3)],
}


class ClasificadorPorReglas(ClasificadorIntenciones):
    def clasificar(self, texto: str) -> tuple[str, float]:
        t = normalizar(texto)
        puntajes = {i: sum(w for rx, w in reglas if re.search(rx, t)) for i, reglas in _REGLAS.items()}
        tiene_numero = extraer_numero(texto) is not None
        if tiene_numero:
            puntajes["estado_contrato"] += 1  # «contrato 045/2026» sin más indicios = pedir su estado
            if puntajes["vencimientos_proximos"] and not puntajes["consultar_documento"]:
                puntajes["estado_contrato"] += 2  # «cuándo vence el contrato 045/2026»
        if puntajes["ayuda"] and max(v for k, v in puntajes.items() if k != "ayuda") >= 2:
            puntajes["ayuda"] = 0  # «hola, qué vence hoy» no es una petición de ayuda
        mejor, pts = max(puntajes.items(), key=lambda kv: kv[1])
        if pts == 0:
            return "desconocida", 0.0
        return mejor, 0.9 if pts >= 3 else 0.7 if pts == 2 else 0.5


class ClasificadorCompuesto(ClasificadorIntenciones):
    """Reglas primero; si no reconocen nada y hay modelo disponible, se le pide que elija una intención."""

    def __init__(self, reglas: ClasificadorIntenciones, modelo: Optional[ModeloDeLenguaje] = None):
        self.reglas, self.modelo = reglas, modelo

    def clasificar(self, texto: str) -> tuple[str, float]:
        intencion, conf = self.reglas.clasificar(texto)
        if conf >= 0.5 or self.modelo is None:
            return intencion, conf
        try:
            instruccion = ("Clasifica el mensaje del usuario en UNA de estas intenciones: " + ", ".join(INTENCIONES) +
                           ". Responde SOLO con el nombre de la intención, o con la palabra desconocida si no encaja.")
            r = normalizar(self.modelo.generar(instruccion, texto)).split(" ")[0].strip(".,;:")
            if r in INTENCIONES:
                return r, 0.6
        except Exception:
            pass
        return "desconocida", 0.0
