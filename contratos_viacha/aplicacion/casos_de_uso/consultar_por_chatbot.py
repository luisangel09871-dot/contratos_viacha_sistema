"""Caso de uso ConsultarPorChatbot.

Flujo: normalizar -> detectar intención -> extraer datos -> validar permisos ->
consultar servicios internos -> redactar la respuesta.

Reglas de oro:
- El chatbot NO toca tablas ni archivos: usa los casos de uso y los puertos.
- Las fechas, estados y plazos salen SIEMPRE de las reglas de vencimiento.
- El modelo de lenguaje (si existe) solo REDACTA datos que ya se obtuvieron. Si falla,
  se responde con plantillas fijas y el chatbot sigue funcionando.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from ...dominio import permisos
from ...dominio.entidades import ConsultaChatbot, Contrato, Usuario
from ...dominio.reglas_vencimiento import dias_restantes, estado_para_contrato
from ..puertos.entrada import ConsultarDocumentos, ConsultarPorChatbot, ConsultarVencimientos
from ..puertos.salida import (ClasificadorIntenciones, ModeloDeLenguaje, RelojDelSistema,
                              RepositorioConsultasChatbot, RepositorioContratos, RepositorioSeguimientos,
                              RepositorioUmbrales)
from ._comun import etiqueta_dias, fmt_fecha, fmt_monto, normalizar

INTENCIONES = ("estado_contrato", "vencimientos_proximos", "contratos_vencidos", "garantias_por_vencer",
               "responsable", "historial", "consultar_documento", "ayuda")

INSTRUCCION = ("Eres el asistente de gestión de contratos del Gobierno Autónomo Municipal de Viacha. "
               "Responde en español, de forma breve, clara y amable, usando ÚNICAMENTE los datos del contexto. "
               "No inventes fechas, montos, nombres ni estados. Conserva las cifras y fechas tal como aparecen. "
               "Si el contexto no contiene la respuesta, di que no la encontraste.")

TEXTO_AYUDA = ("Puedo ayudarte con estas consultas:\n"
               "• Estado de un contrato: «¿Cómo está el contrato 045/2026?»\n"
               "• Vencimientos próximos: «¿Qué vence esta semana?»\n"
               "• Contratos vencidos: «¿Hay contratos vencidos?»\n"
               "• Garantías: «¿Qué boletas vencen este mes?»\n"
               "• Responsable de un contrato: «¿Quién lleva el contrato 045/2026?»\n"
               "• Historial: «¿Qué se hizo con el contrato 045/2026?»\n"
               "• Documentos: «¿Qué dice el contrato 045/2026 sobre las multas?»\n"
               "También puedes adjuntar un documento a un contrato con el botón del clip.")

_NUMERO = re.compile(r"\b(\d{1,4})\s*/\s*(\d{4})\b")


def extraer_numero(texto: str) -> Optional[tuple[str, str]]:
    m = _NUMERO.search(texto or "")
    return (m.group(1), m.group(2)) if m else None


def extraer_dias(texto: str, por_defecto: int = 30) -> int:
    t = normalizar(texto)
    m = re.search(r"(\d+)\s*(dias?|semanas?|meses|mes)\b", t)
    if m:
        n, u = int(m.group(1)), m.group(2)
        return min(n * (7 if u.startswith("semana") else 30 if u.startswith("mes") else 1), 365)
    if "hoy" in t:
        return 0
    if "manana" in t:
        return 1
    if "semana" in t:
        return 7
    if "quincena" in t:
        return 15
    if "mes" in t:
        return 30
    return por_defecto


@dataclass
class _Resultado:
    texto: str
    contexto: str = ""
    aclaracion: bool = False
    redactable: bool = True
    fuentes: list = field(default_factory=list)


class ConsultarPorChatbotCU(ConsultarPorChatbot):
    def __init__(self, clasificador: ClasificadorIntenciones, vencimientos: ConsultarVencimientos,
                 documentos: ConsultarDocumentos, contratos: RepositorioContratos,
                 seguimientos: RepositorioSeguimientos, umbrales: RepositorioUmbrales,
                 consultas: RepositorioConsultasChatbot, reloj: RelojDelSistema,
                 modelo: Optional[ModeloDeLenguaje] = None):
        self.clasificador, self.vencimientos, self.documentos = clasificador, vencimientos, documentos
        self.contratos, self.seguimientos, self.umbrales = contratos, seguimientos, umbrales
        self.consultas, self.reloj, self.modelo = consultas, reloj, modelo

    # ---------- utilidades ----------
    def _buscar_contrato(self, mensaje: str) -> tuple[Optional[tuple[str, str]], Optional[Contrato]]:
        num = extraer_numero(mensaje)
        if not num:
            return None, None
        n, anio = num
        for cand in (f"{n}/{anio}", f"{int(n):03d}/{anio}", f"{int(n):04d}/{anio}", f"{int(n)}/{anio}"):
            c = self.contratos.obtener_por_numero(cand)
            if c:
                return num, c
        return num, None

    def _estado(self, c: Contrato):
        return estado_para_contrato(c.estado, c.fecha_vencimiento, self.reloj.hoy(), self.umbrales.obtener())

    def _contrato_o_aclaracion(self, actor: Usuario, mensaje: str):
        num, c = self._buscar_contrato(mensaje)
        if num is None:
            return None, _Resultado("¿De qué contrato? Indícame el número, por ejemplo 045/2026.",
                                    aclaracion=True, redactable=False)
        if c is None:
            return None, _Resultado(f"No encontré el contrato {num[0]}/{num[1]}. Revisa el número e inténtalo de nuevo.",
                                    redactable=False)
        if not permisos.puede_ver_contrato(actor, c):
            return None, _Resultado(f"No tienes acceso al contrato {c.numero}.", redactable=False)
        return c, None

    # ---------- manejadores por intención ----------
    def _estado_contrato(self, actor: Usuario, mensaje: str) -> _Resultado:
        c, falta = self._contrato_o_aclaracion(actor, mensaje)
        if falta:
            return falta
        dias = dias_restantes(c.fecha_vencimiento, self.reloj.hoy())
        texto = (f"Contrato {c.numero}: {c.objeto}. Contratista: {c.contratista_nombre}. "
                 f"Responsable: {c.responsable_nombre}. Vigencia: {fmt_fecha(c.fecha_inicio)} al "
                 f"{fmt_fecha(c.fecha_vencimiento)} ({etiqueta_dias(dias)}). Estado: {self._estado(c).etiqueta}. "
                 f"Monto: {fmt_monto(c.monto)}.")
        return _Resultado(texto, texto)

    def _responsable(self, actor: Usuario, mensaje: str) -> _Resultado:
        c, falta = self._contrato_o_aclaracion(actor, mensaje)
        if falta:
            return falta
        t = f"El responsable del contrato {c.numero} es {c.responsable_nombre}."
        return _Resultado(t, t)

    def _historial(self, actor: Usuario, mensaje: str) -> _Resultado:
        c, falta = self._contrato_o_aclaracion(actor, mensaje)
        if falta:
            return falta
        segs = self.seguimientos.listar_por_contrato(c.id)[:5]
        if not segs:
            return _Resultado(f"El contrato {c.numero} todavía no tiene acciones registradas.", redactable=False)
        lineas = [f"- {fmt_fecha(self.reloj.fecha_local(s.fecha))}, {s.usuario_nombre}: {s.accion}" for s in segs]
        t = f"Últimas acciones registradas en el contrato {c.numero}:\n" + "\n".join(lineas)
        return _Resultado(t, t)

    def _listar_contratos(self, contratos: list[Contrato], encabezado: str, vacio: str) -> _Resultado:
        if not contratos:
            return _Resultado(vacio, redactable=False)
        hoy = self.reloj.hoy()
        lineas = [f"- {c.numero}: {c.objeto[:70]} ({etiqueta_dias(dias_restantes(c.fecha_vencimiento, hoy))}, "
                  f"{fmt_fecha(c.fecha_vencimiento)}). Responsable: {c.responsable_nombre}." for c in contratos[:10]]
        extra = f"\n(Se muestran 10 de {len(contratos)}.)" if len(contratos) > 10 else ""
        t = f"{encabezado} ({len(contratos)}):\n" + "\n".join(lineas) + extra
        return _Resultado(t, t)

    def _vencimientos(self, actor: Usuario, mensaje: str) -> _Resultado:
        dias = extraer_dias(mensaje, 30)
        cuando = "hoy" if dias == 0 else "esta semana" if dias == 7 else f"en los próximos {dias} días"
        return self._listar_contratos(self.vencimientos.vencen_en(actor, dias), f"Contratos que vencen {cuando}",
                                      f"No hay contratos que venzan {cuando}.")

    def _vencidos(self, actor: Usuario, mensaje: str) -> _Resultado:
        return self._listar_contratos(self.vencimientos.vencidos(actor), "Contratos vencidos",
                                      "No hay contratos vencidos.")

    def _garantias(self, actor: Usuario, mensaje: str) -> _Resultado:
        dias = extraer_dias(mensaje, 30)
        gar = self.vencimientos.garantias_por_vencer(actor, dias)
        cuando = "esta semana" if dias == 7 else f"en los próximos {dias} días"
        if not gar:
            return _Resultado(f"No hay garantías que venzan {cuando}.", redactable=False)
        hoy = self.reloj.hoy()
        lineas = [f"- {g.tipo.capitalize()} del contrato {g.contrato_numero}: vence el {fmt_fecha(g.fecha_vencimiento)} "
                  f"({etiqueta_dias(dias_restantes(g.fecha_vencimiento, hoy))})." for g in gar[:10]]
        t = f"Garantías que vencen {cuando} ({len(gar)}):\n" + "\n".join(lineas)
        return _Resultado(t, t)

    def _documento(self, actor: Usuario, mensaje: str) -> _Resultado:
        num, c = self._buscar_contrato(mensaje)
        id_contrato = None
        if num and c and permisos.puede_ver_contrato(actor, c):
            id_contrato = c.id
        frag = self.documentos.buscar_fragmentos(actor, mensaje, id_contrato)
        if not frag:
            return _Resultado("No encontré información sobre eso en los documentos a los que tienes acceso.",
                              redactable=False)
        lineas = [f"- «{f['fragmento']}»" for f in frag]
        con_fuente = [f"- «{f['fragmento']}» (documento «{f['documento']}», contrato {f['contrato_numero']})" for f in frag]
        fuentes = [{"documento": f["documento"], "contrato": f["contrato_numero"]} for f in frag]
        return _Resultado("Esto es lo que encontré en los documentos:\n" + "\n".join(lineas),
                          "Fragmentos de documentos:\n" + "\n".join(con_fuente) + f"\nPregunta del usuario: {mensaje}",
                          fuentes=fuentes)

    # ---------- flujo principal ----------
    def consultar(self, actor: Usuario, mensaje: str) -> dict[str, Any]:
        mensaje = re.sub(r"\s+", " ", (mensaje or "")).strip()[:500]
        if not mensaje:
            res, intencion = _Resultado("Escribe tu pregunta, por ejemplo: «¿Qué vence esta semana?»",
                                        aclaracion=True, redactable=False), "aclaracion"
        else:
            intencion, confianza = self.clasificador.clasificar(mensaje)
            manejadores = {"estado_contrato": self._estado_contrato, "vencimientos_proximos": self._vencimientos,
                           "contratos_vencidos": self._vencidos, "garantias_por_vencer": self._garantias,
                           "responsable": self._responsable, "historial": self._historial,
                           "consultar_documento": self._documento}
            if intencion == "ayuda":
                res = _Resultado(TEXTO_AYUDA, redactable=False)
            elif intencion in manejadores and confianza >= 0.5:
                res = manejadores[intencion](actor, mensaje)
            else:
                intencion = "desconocida"
                res = _Resultado("No estoy seguro de haber entendido tu pregunta. ¿Puedes reformularla?\n\n" + TEXTO_AYUDA,
                                 aclaracion=True, redactable=False)
        texto, adaptador = res.texto, "plantillas"
        if self.modelo is not None and res.redactable and not res.aclaracion:
            try:
                redactado = self.modelo.generar(INSTRUCCION, res.contexto or res.texto)
                if redactado and redactado.strip():
                    texto, adaptador = redactado.strip(), self.modelo.nombre
            except Exception:  # cuota, red, tiempo de espera: se responde con plantillas
                texto, adaptador = res.texto, "plantillas"
        if res.fuentes:  # la fuente siempre se muestra, la redacte quien la redacte
            texto += "\n\nFuente: " + "; ".join(sorted({f"«{f['documento']}» (contrato {f['contrato']})" for f in res.fuentes}))
        self.consultas.guardar(ConsultaChatbot(None, actor.id, mensaje, intencion, texto, adaptador, self.reloj.ahora()))
        return {"texto": texto, "intencion": intencion, "adaptador": adaptador,
                "aclaracion": res.aclaracion, "fuentes": res.fuentes}
