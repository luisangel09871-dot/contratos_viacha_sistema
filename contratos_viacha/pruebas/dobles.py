"""Dobles de prueba: repositorios EN MEMORIA, reloj falso y correo simulado.
Permiten probar dominio y casos de uso SIN base de datos ni servidor (ventaja de la arquitectura hexagonal)."""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Optional

from contratos_viacha.aplicacion.casos_de_uso.administrar_usuarios import AdministrarUsuariosCU
from contratos_viacha.aplicacion.casos_de_uso.consultar_por_chatbot import ConsultarPorChatbotCU
from contratos_viacha.aplicacion.casos_de_uso.consultar_vencimientos import ConsultarVencimientosCU
from contratos_viacha.aplicacion.casos_de_uso.documentos import ConsultarDocumentosCU, SubirDocumentoCU
from contratos_viacha.aplicacion.casos_de_uso.gestionar_contratos import GestionarContratosCU
from contratos_viacha.aplicacion.casos_de_uso.registrar_seguimiento import RegistrarSeguimientoCU
from contratos_viacha.aplicacion.casos_de_uso.revisar_vencimientos import EjecutarRevisionDiariaCU
from contratos_viacha.aplicacion.puertos import salida as p
from contratos_viacha.dominio.entidades import (Contratista, Contrato, EstadoContrato, RegistroAuditoriaEntidad, Rol,
                                                Umbrales, Usuario)


class RelojPuro(p.RelojDelSistema):
    def __init__(self, hoy: date):
        self._hoy = hoy

    def hoy(self): return self._hoy
    def ahora(self): return datetime(self._hoy.year, self._hoy.month, self._hoy.day, 9, 0, 0)
    def fecha_local(self, momento): return momento.date()
    def avanzar(self, dias): self._hoy += timedelta(days=dias)


class Notificador(p.NotificadorCorreo):
    def __init__(self, funciona=True):
        self.funciona, self.enviados = funciona, []

    def enviar(self, destinatario, asunto, cuerpo):
        if self.funciona:
            self.enviados.append((destinatario, asunto, cuerpo))
        return self.funciona


class Almacen(p.AlmacenDocumentos):
    def __init__(self): self.archivos = {}
    def guardar(self, nombre_archivo, contenido): self.archivos[nombre_archivo] = contenido
    def leer(self, nombre_archivo): return self.archivos[nombre_archivo]


class Extractor(p.ExtractorTexto):
    def extraer(self, tipo, contenido): return contenido.decode("utf-8", errors="ignore")


class ModeloFalso(p.ModeloDeLenguaje):
    def __init__(self, respuesta="Respuesta redactada por el modelo.", falla=False):
        self.respuesta, self.falla, self.nombre, self.llamadas = respuesta, falla, "modelo-falso", []

    def generar(self, instruccion, contexto):
        self.llamadas.append((instruccion, contexto))
        if self.falla:
            raise p.ErrorModeloLenguaje("falla simulada")
        return self.respuesta


class _Secuencia:
    def __init__(self): self.n = 0
    def siguiente(self):
        self.n += 1
        return self.n


class RepoContratos(p.RepositorioContratos):
    def __init__(self, entorno): self.e, self.datos, self.seq = entorno, {}, _Secuencia()

    def _con_nombres(self, c):
        c = replace(c)
        c.contratista_nombre = (self.e.contratistas.datos.get(c.id_contratista).razon_social
                                if c.id_contratista in self.e.contratistas.datos else "")
        u = self.e.usuarios.datos.get(c.id_responsable)
        c.responsable_nombre = u.nombre_completo if u else ""
        c.tipo_nombre = dict(self.e.tipos.listar()).get(c.id_tipo, "")
        return c

    def guardar(self, c):
        c = replace(c)
        c.id = c.id or self.seq.siguiente()
        self.datos[c.id] = c
        return self._con_nombres(c)

    def obtener(self, id_contrato): return self._con_nombres(self.datos[id_contrato]) if id_contrato in self.datos else None
    def obtener_por_numero(self, numero):
        return next((self._con_nombres(c) for c in self.datos.values() if c.numero.lower() == numero.strip().lower()), None)

    def buscar(self, f, id_responsable=None):
        r = []
        for c in self.datos.values():
            if id_responsable is not None and c.id_responsable != id_responsable: continue
            if f.id_tipo and c.id_tipo != f.id_tipo: continue
            if f.id_contratista and c.id_contratista != f.id_contratista: continue
            if f.id_responsable and c.id_responsable != f.id_responsable: continue
            if f.vence_desde and c.fecha_vencimiento < f.vence_desde: continue
            if f.vence_hasta and c.fecha_vencimiento > f.vence_hasta: continue
            if f.texto and f.texto.lower() not in (c.numero + c.objeto).lower(): continue
            r.append(self._con_nombres(c))
        return sorted(r, key=lambda c: c.fecha_vencimiento)

    def listar_activos(self): return [self._con_nombres(c) for c in self.datos.values() if not c.estado.es_final]
    def actualizar_estado(self, id_contrato, estado): self.datos[id_contrato].estado = estado


class RepoContratistas(p.RepositorioContratistas):
    def __init__(self): self.datos, self.seq = {}, _Secuencia()
    def guardar(self, c):
        c = replace(c); c.id = c.id or self.seq.siguiente(); self.datos[c.id] = c; return c
    def obtener(self, id_): return self.datos.get(id_)
    def obtener_por_nit(self, nit): return next((c for c in self.datos.values() if c.nit == nit), None)
    def listar(self): return list(self.datos.values())


class RepoTipos(p.RepositorioTiposContrato):
    def listar(self): return [(1, "Obras"), (2, "Bienes"), (3, "Servicios generales"), (4, "Consultoría")]


class RepoGarantias(p.RepositorioGarantias):
    def __init__(self, entorno): self.e, self.datos, self.seq = entorno, [], _Secuencia()
    def guardar(self, g):
        g = replace(g); g.id = self.seq.siguiente()
        c = self.e.contratos.datos.get(g.id_contrato); g.contrato_numero = c.numero if c else ""
        self.datos.append(g); return g
    def listar_por_contrato(self, id_contrato): return [g for g in self.datos if g.id_contrato == id_contrato]
    def por_vencer(self, desde, hasta, id_responsable=None):
        r = []
        for g in self.datos:
            c = self.e.contratos.datos[g.id_contrato]
            if c.estado.es_final or not (desde <= g.fecha_vencimiento <= hasta): continue
            if id_responsable is not None and c.id_responsable != id_responsable: continue
            r.append(g)
        return r


class RepoAlertas(p.RepositorioAlertas):
    def __init__(self, entorno): self.e, self.datos, self.seq = entorno, [], _Secuencia()
    def guardar(self, a):
        a = replace(a); a.id = self.seq.siguiente(); self.datos.append(a); return a
    def niveles_emitidos(self, id_contrato): return {a.nivel for a in self.datos if a.id_contrato == id_contrato}
    def critico_emitido_en(self, id_contrato, dia):
        return any(a.id_contrato == id_contrato and a.nivel == "critico" and a.fecha_emision.date() == dia for a in self.datos)
    def listar(self, id_responsable=None, solo_no_leidas=False, limite=200):
        r = [a for a in self.datos if (id_responsable is None or self.e.contratos.datos[a.id_contrato].id_responsable == id_responsable)
             and (not solo_no_leidas or not a.leida)]
        return list(reversed(r))[:limite]
    def listar_por_contrato(self, id_contrato): return [a for a in reversed(self.datos) if a.id_contrato == id_contrato]
    def marcar_leida(self, id_alerta):
        for a in self.datos:
            if a.id == id_alerta: a.leida = True
    def obtener(self, id_alerta): return next((a for a in self.datos if a.id == id_alerta), None)


class RepoSeguimientos(p.RepositorioSeguimientos):
    def __init__(self, entorno): self.e, self.datos, self.seq = entorno, [], _Secuencia()
    def guardar(self, s):
        s = replace(s); s.id = self.seq.siguiente(); s.usuario_nombre = self.e.usuarios.datos[s.id_usuario].nombre_completo
        self.datos.append(s); return s
    def listar_por_contrato(self, id_contrato): return [s for s in reversed(self.datos) if s.id_contrato == id_contrato]


class RepoUsuarios(p.RepositorioUsuarios):
    def __init__(self): self.datos, self.claves, self.seq = {}, {}, _Secuencia()
    def obtener(self, id_): return self.datos.get(id_)
    def por_correo(self, correo): return next((u for u in self.datos.values() if u.correo == correo.strip().lower()), None)
    def listar(self): return list(self.datos.values())
    def crear(self, u, password):
        u = replace(u); u.id = self.seq.siguiente(); self.datos[u.id] = u; self.claves[u.id] = password; return u
    def actualizar(self, u): self.datos[u.id] = replace(u); return u
    def cambiar_password(self, id_usuario, password): self.claves[id_usuario] = password
    def verificar_credenciales(self, correo, password):
        u = self.por_correo(correo)
        return u if u and self.claves[u.id] == password else None


class RepoDocumentos(p.RepositorioDocumentos):
    def __init__(self, entorno): self.e, self.datos, self.seq = entorno, [], _Secuencia()
    def guardar(self, d):
        d = replace(d); d.id = self.seq.siguiente(); d.subido_por_nombre = self.e.usuarios.datos[d.subido_por].nombre_completo
        self.datos.append(d); return d
    def obtener(self, id_): return next((d for d in self.datos if d.id == id_), None)
    def listar_por_contrato(self, id_contrato): return [d for d in self.datos if d.id_contrato == id_contrato]
    def listar_accesibles(self, id_responsable=None):
        return [d for d in self.datos if id_responsable is None or self.e.contratos.datos[d.id_contrato].id_responsable == id_responsable]


class RepoUmbrales(p.RepositorioUmbrales):
    def __init__(self): self.u = Umbrales()
    def obtener(self): return self.u
    def guardar(self, u): self.u = u


class RepoConsultas(p.RepositorioConsultasChatbot):
    def __init__(self): self.datos = []
    def guardar(self, c): self.datos.append(c)


class Auditoria(p.RegistroAuditoria):
    def __init__(self, reloj): self.reloj, self.datos = reloj, []
    def registrar(self, id_usuario, tabla, operacion, detalle=""):
        self.datos.append(RegistroAuditoriaEntidad(len(self.datos) + 1, id_usuario, tabla, operacion, detalle, self.reloj.ahora()))
    def listar(self, limite=200): return list(reversed(self.datos))[:limite]


class Transaccion(p.Transaccion):
    def atomico(self): return nullcontext()


class Entorno:
    """Todo el sistema conectado a dobles en memoria."""

    def __init__(self, hoy: date = date(2026, 11, 10), modelo=None, notificador_funciona=True):
        from contratos_viacha.adaptadores.salida.clasificador import ClasificadorCompuesto, ClasificadorPorReglas
        self.reloj = RelojPuro(hoy)
        self.usuarios, self.contratistas, self.tipos = RepoUsuarios(), RepoContratistas(), RepoTipos()
        self.contratos, self.garantias = RepoContratos(self), RepoGarantias(self)
        self.alertas, self.seguimientos, self.documentos = RepoAlertas(self), RepoSeguimientos(self), RepoDocumentos(self)
        self.umbrales, self.consultas, self.auditoria = RepoUmbrales(), RepoConsultas(), Auditoria(self.reloj)
        self.notificador, self.almacen, self.modelo = Notificador(notificador_funciona), Almacen(), modelo
        tx = Transaccion()
        self.gestionar = GestionarContratosCU(self.contratos, self.contratistas, self.garantias, self.alertas, self.seguimientos,
                                              self.documentos, self.usuarios, self.tipos, self.umbrales, self.reloj, self.auditoria, tx)
        self.consultar = ConsultarVencimientosCU(self.contratos, self.garantias, self.alertas, self.umbrales, self.reloj)
        self.seguimiento = RegistrarSeguimientoCU(self.contratos, self.seguimientos, self.alertas, self.reloj, self.auditoria, tx)
        self.revision = EjecutarRevisionDiariaCU(self.contratos, self.garantias, self.alertas, self.usuarios, self.notificador,
                                                 self.umbrales, self.reloj, self.auditoria)
        self.admin_usuarios = AdministrarUsuariosCU(self.usuarios, self.umbrales, self.auditoria, tx)
        self.subir = SubirDocumentoCU(self.contratos, self.documentos, self.almacen, Extractor(), self.reloj, self.auditoria, tx)
        self.docs = ConsultarDocumentosCU(self.contratos, self.documentos, self.almacen, self.auditoria)
        self.chatbot = ConsultarPorChatbotCU(ClasificadorCompuesto(ClasificadorPorReglas(), modelo), self.consultar, self.docs,
                                             self.contratos, self.seguimientos, self.umbrales, self.consultas, self.reloj, modelo)
        self.contratista = self.contratistas.guardar(Contratista(None, "Constructora de Prueba S.R.L.", "123"))
        self.admin = self.usuario(Rol.ADMINISTRADOR, "Admin")
        self.funcionario = self.usuario(Rol.FUNCIONARIO, "Funcionaria")
        self.resp1 = self.usuario(Rol.RESPONSABLE, "Responsable Uno")
        self.resp2 = self.usuario(Rol.RESPONSABLE, "Responsable Dos")
        self.autoridad = self.usuario(Rol.AUTORIDAD, "Autoridad")

    def usuario(self, rol: Rol, nombre: str) -> Usuario:
        return self.usuarios.crear(Usuario(None, nombre, f"{nombre.lower().replace(' ', '')}@prueba.test", rol, True), "clave-segura-1")

    def contrato(self, dias: int, numero: str = None, responsable: Usuario = None, **extra) -> Contrato:
        """Registra un contrato que vence dentro de `dias` días (negativo = ya vencido)."""
        hoy = self.reloj.hoy()
        n = numero or f"{len(self.contratos.datos) + 1:03d}/2026"
        datos = dict(numero=n, objeto=f"Objeto del contrato {n}", id_tipo=1, id_contratista=self.contratista.id,
                     id_responsable=(responsable or self.resp1).id, monto=1000, fecha_inicio=hoy + timedelta(days=dias - 180),
                     fecha_vencimiento=hoy + timedelta(days=dias))
        datos.update(extra)
        return self.gestionar.registrar_contrato(self.funcionario, datos)
