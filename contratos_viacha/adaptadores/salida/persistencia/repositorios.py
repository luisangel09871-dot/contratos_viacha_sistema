"""Adaptadores de salida: repositorios sobre PostgreSQL con el ORM de Django.
Convierten entre modelos Django y entidades de dominio. El dominio nunca ve un modelo."""
from __future__ import annotations

from datetime import date
from typing import Optional

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Q

from ....aplicacion.puertos import salida as p
from ....dominio.entidades import (Alerta, ConsultaChatbot, Contratista, Contrato, Documento, EstadoContrato,
                                   FiltroContratos, Garantia, RegistroAuditoriaEntidad, Rol, Seguimiento, Umbrales,
                                   Usuario)
from . import models as m

_HASH_FALSO = make_password("contrasena-inexistente")  # iguala el tiempo de respuesta si el usuario no existe


# ---------------- conversión modelo -> entidad ----------------
def a_usuario(x: m.UsuarioModelo) -> Usuario:
    return Usuario(x.id, x.nombre_completo, x.correo, Rol(x.rol.nombre), x.activo, x.unidad_id)


def a_contrato(x: m.ContratoModelo) -> Contrato:
    return Contrato(x.id, x.numero, x.objeto, x.tipo_id, x.contratista_id, x.responsable_id, x.monto or 0,
                    x.fecha_inicio, x.fecha_vencimiento, EstadoContrato(x.estado), x.tipo.nombre,
                    x.contratista.razon_social, x.responsable.nombre_completo)


def a_garantia(x: m.GarantiaModelo) -> Garantia:
    return Garantia(x.id, x.contrato_id, x.tipo, x.fecha_vencimiento, x.contrato.numero)


def a_alerta(x: m.AlertaModelo) -> Alerta:
    return Alerta(x.id, x.contrato_id, x.nivel, x.canal, x.fecha_emision, x.leida, x.mensaje, x.contrato.numero)


def a_documento(x: m.DocumentoModelo, con_texto: bool = False) -> Documento:
    return Documento(x.id, x.contrato_id, x.nombre_original, x.nombre_archivo, x.tipo, x.tamano, x.subido_por_id,
                     x.fecha, x.texto_extraido if con_texto else "", x.contrato.numero,
                     x.subido_por.nombre_completo)


_CONTRATO_QS = m.ContratoModelo.objects.select_related("tipo", "contratista", "responsable")


class RepositorioContratosORM(p.RepositorioContratos):
    def guardar(self, c: Contrato) -> Contrato:
        campos = dict(numero=c.numero, objeto=c.objeto, tipo_id=c.id_tipo, contratista_id=c.id_contratista,
                      responsable_id=c.id_responsable, monto=c.monto, fecha_inicio=c.fecha_inicio,
                      fecha_vencimiento=c.fecha_vencimiento, estado=c.estado.value)
        if c.id:
            m.ContratoModelo.objects.filter(pk=c.id).update(**campos)
            pk = c.id
        else:
            pk = m.ContratoModelo.objects.create(**campos).pk
        return a_contrato(_CONTRATO_QS.get(pk=pk))

    def obtener(self, id_contrato: int) -> Optional[Contrato]:
        x = _CONTRATO_QS.filter(pk=id_contrato).first()
        return a_contrato(x) if x else None

    def obtener_por_numero(self, numero: str) -> Optional[Contrato]:
        x = _CONTRATO_QS.filter(numero__iexact=numero.strip()).first()
        return a_contrato(x) if x else None

    def buscar(self, f: FiltroContratos, id_responsable: Optional[int] = None) -> list[Contrato]:
        # El estado NO se filtra aquí: el caso de uso lo filtra ya recalculado con la fecha de hoy.
        qs = _CONTRATO_QS.all()
        if id_responsable is not None:
            qs = qs.filter(responsable_id=id_responsable)
        if f.id_tipo:
            qs = qs.filter(tipo_id=f.id_tipo)
        if f.id_contratista:
            qs = qs.filter(contratista_id=f.id_contratista)
        if f.id_responsable:
            qs = qs.filter(responsable_id=f.id_responsable)
        if f.vence_desde:
            qs = qs.filter(fecha_vencimiento__gte=f.vence_desde)
        if f.vence_hasta:
            qs = qs.filter(fecha_vencimiento__lte=f.vence_hasta)
        if f.texto:
            t = f.texto.strip()
            qs = qs.filter(Q(numero__icontains=t) | Q(objeto__icontains=t) | Q(contratista__razon_social__icontains=t))
        return [a_contrato(x) for x in qs.order_by("fecha_vencimiento", "numero")]

    def listar_activos(self) -> list[Contrato]:
        qs = _CONTRATO_QS.exclude(estado__in=[EstadoContrato.RENOVADO.value, EstadoContrato.TERMINADO.value])
        return [a_contrato(x) for x in qs.order_by("fecha_vencimiento")]

    def actualizar_estado(self, id_contrato: int, estado: EstadoContrato) -> None:
        m.ContratoModelo.objects.filter(pk=id_contrato).update(estado=estado.value)


class RepositorioContratistasORM(p.RepositorioContratistas):
    @staticmethod
    def _a(x): return Contratista(x.id, x.razon_social, x.nit, x.correo_contacto)

    def guardar(self, c: Contratista) -> Contratista:
        if c.id:
            m.ContratistaModelo.objects.filter(pk=c.id).update(razon_social=c.razon_social, nit=c.nit,
                                                                correo_contacto=c.correo_contacto)
            return self._a(m.ContratistaModelo.objects.get(pk=c.id))
        return self._a(m.ContratistaModelo.objects.create(razon_social=c.razon_social, nit=c.nit,
                                                          correo_contacto=c.correo_contacto))

    def obtener(self, id_contratista: int) -> Optional[Contratista]:
        x = m.ContratistaModelo.objects.filter(pk=id_contratista).first()
        return self._a(x) if x else None

    def obtener_por_nit(self, nit: str) -> Optional[Contratista]:
        x = m.ContratistaModelo.objects.filter(nit=nit).first()
        return self._a(x) if x else None

    def listar(self) -> list[Contratista]:
        return [self._a(x) for x in m.ContratistaModelo.objects.order_by("razon_social")]


class RepositorioTiposContratoORM(p.RepositorioTiposContrato):
    def listar(self) -> list[tuple[int, str]]:
        return list(m.TipoContratoModelo.objects.order_by("id").values_list("id", "nombre"))


class RepositorioGarantiasORM(p.RepositorioGarantias):
    def guardar(self, g: Garantia) -> Garantia:
        x = m.GarantiaModelo.objects.create(contrato_id=g.id_contrato, tipo=g.tipo, fecha_vencimiento=g.fecha_vencimiento)
        return a_garantia(m.GarantiaModelo.objects.select_related("contrato").get(pk=x.pk))

    def listar_por_contrato(self, id_contrato: int) -> list[Garantia]:
        qs = m.GarantiaModelo.objects.select_related("contrato").filter(contrato_id=id_contrato).order_by("fecha_vencimiento")
        return [a_garantia(x) for x in qs]

    def por_vencer(self, desde: date, hasta: date, id_responsable: Optional[int] = None) -> list[Garantia]:
        qs = (m.GarantiaModelo.objects.select_related("contrato")
              .filter(fecha_vencimiento__range=(desde, hasta))
              .exclude(contrato__estado__in=[EstadoContrato.RENOVADO.value, EstadoContrato.TERMINADO.value]))
        if id_responsable is not None:
            qs = qs.filter(contrato__responsable_id=id_responsable)
        return [a_garantia(x) for x in qs.order_by("fecha_vencimiento")]


class RepositorioAlertasORM(p.RepositorioAlertas):
    def guardar(self, a: Alerta) -> Alerta:
        x = m.AlertaModelo.objects.create(contrato_id=a.id_contrato, nivel=a.nivel, mensaje=a.mensaje,
                                          fecha_emision=a.fecha_emision, canal=a.canal, leida=a.leida)
        return a_alerta(m.AlertaModelo.objects.select_related("contrato").get(pk=x.pk))

    def niveles_emitidos(self, id_contrato: int) -> set[str]:
        return set(m.AlertaModelo.objects.filter(contrato_id=id_contrato).values_list("nivel", flat=True))

    def critico_emitido_en(self, id_contrato: int, dia: date) -> bool:
        return m.AlertaModelo.objects.filter(contrato_id=id_contrato, nivel="critico", fecha_emision__date=dia).exists()

    def listar(self, id_responsable: Optional[int] = None, solo_no_leidas: bool = False, limite: int = 200) -> list[Alerta]:
        qs = m.AlertaModelo.objects.select_related("contrato")
        if id_responsable is not None:
            qs = qs.filter(contrato__responsable_id=id_responsable)
        if solo_no_leidas:
            qs = qs.filter(leida=False)
        return [a_alerta(x) for x in qs.order_by("-fecha_emision", "-id")[:limite]]

    def listar_por_contrato(self, id_contrato: int) -> list[Alerta]:
        qs = m.AlertaModelo.objects.select_related("contrato").filter(contrato_id=id_contrato).order_by("-fecha_emision", "-id")
        return [a_alerta(x) for x in qs]

    def marcar_leida(self, id_alerta: int) -> None:
        m.AlertaModelo.objects.filter(pk=id_alerta).update(leida=True)

    def obtener(self, id_alerta: int) -> Optional[Alerta]:
        x = m.AlertaModelo.objects.select_related("contrato").filter(pk=id_alerta).first()
        return a_alerta(x) if x else None


class RepositorioSeguimientosORM(p.RepositorioSeguimientos):
    @staticmethod
    def _a(x): return Seguimiento(x.id, x.contrato_id, x.usuario_id, x.accion, x.fecha, x.usuario.nombre_completo)

    def guardar(self, s: Seguimiento) -> Seguimiento:
        x = m.SeguimientoModelo.objects.create(contrato_id=s.id_contrato, usuario_id=s.id_usuario, accion=s.accion, fecha=s.fecha)
        return self._a(m.SeguimientoModelo.objects.select_related("usuario").get(pk=x.pk))

    def listar_por_contrato(self, id_contrato: int) -> list[Seguimiento]:
        qs = m.SeguimientoModelo.objects.select_related("usuario").filter(contrato_id=id_contrato).order_by("-fecha", "-id")
        return [self._a(x) for x in qs]


class RepositorioUsuariosORM(p.RepositorioUsuarios):
    _QS = m.UsuarioModelo.objects.select_related("rol")

    def obtener(self, id_usuario: int) -> Optional[Usuario]:
        x = self._QS.filter(pk=id_usuario).first()
        return a_usuario(x) if x else None

    def por_correo(self, correo: str) -> Optional[Usuario]:
        x = self._QS.filter(correo__iexact=correo.strip()).first()
        return a_usuario(x) if x else None

    def listar(self) -> list[Usuario]:
        return [a_usuario(x) for x in self._QS.order_by("nombre_completo")]

    def crear(self, u: Usuario, password: str) -> Usuario:
        rol = m.RolModelo.objects.get(nombre=u.rol.value)
        x = m.UsuarioModelo.objects.create_user(correo=u.correo, password=password, nombre_completo=u.nombre_completo,
                                                rol=rol, activo=u.activo, unidad_id=u.id_unidad)
        return a_usuario(self._QS.get(pk=x.pk))

    def actualizar(self, u: Usuario) -> Usuario:
        rol = m.RolModelo.objects.get(nombre=u.rol.value)
        m.UsuarioModelo.objects.filter(pk=u.id).update(nombre_completo=u.nombre_completo, rol=rol, activo=u.activo)
        return a_usuario(self._QS.get(pk=u.id))

    def cambiar_password(self, id_usuario: int, password: str) -> None:
        x = m.UsuarioModelo.objects.get(pk=id_usuario)
        x.set_password(password)
        x.save(update_fields=["password"])

    def verificar_credenciales(self, correo: str, password: str) -> Optional[Usuario]:
        x = self._QS.filter(correo__iexact=correo.strip()).first()
        if x is None:
            check_password(password, _HASH_FALSO)
            return None
        return a_usuario(x) if check_password(password, x.password) else None


class RepositorioDocumentosORM(p.RepositorioDocumentos):
    _QS = m.DocumentoModelo.objects.select_related("contrato", "subido_por")

    def guardar(self, d: Documento) -> Documento:
        x = m.DocumentoModelo.objects.create(contrato_id=d.id_contrato, nombre_original=d.nombre_original,
                                             nombre_archivo=d.nombre_archivo, tipo=d.tipo, tamano=d.tamano,
                                             subido_por_id=d.subido_por, fecha=d.fecha, texto_extraido=d.texto_extraido)
        return a_documento(self._QS.get(pk=x.pk))

    def obtener(self, id_documento: int) -> Optional[Documento]:
        x = self._QS.filter(pk=id_documento).first()
        return a_documento(x) if x else None

    def listar_por_contrato(self, id_contrato: int) -> list[Documento]:
        return [a_documento(x) for x in self._QS.filter(contrato_id=id_contrato).order_by("-fecha")]

    def listar_accesibles(self, id_responsable: Optional[int] = None) -> list[Documento]:
        qs = self._QS.all()
        if id_responsable is not None:
            qs = qs.filter(contrato__responsable_id=id_responsable)
        return [a_documento(x, con_texto=True) for x in qs]


class RepositorioUmbralesORM(p.RepositorioUmbrales):
    def obtener(self) -> Umbrales:
        x = m.UmbralModelo.objects.order_by("id").first()
        return Umbrales(x.dias_proximo, x.dias_critico, x.aviso_1, x.aviso_2) if x else Umbrales()

    def guardar(self, u: Umbrales) -> None:
        m.UmbralModelo.objects.update_or_create(id=1, defaults=dict(dias_proximo=u.dias_proximo, dias_critico=u.dias_critico,
                                                                    aviso_1=u.aviso_1, aviso_2=u.aviso_2))


class RepositorioConsultasChatbotORM(p.RepositorioConsultasChatbot):
    def guardar(self, c: ConsultaChatbot) -> None:
        m.ConsultaChatbotModelo.objects.create(usuario_id=c.id_usuario, mensaje=c.mensaje, intencion=c.intencion,
                                               respuesta=c.respuesta, adaptador=c.adaptador, fecha_hora=c.fecha_hora)


class RegistroAuditoriaORM(p.RegistroAuditoria):
    def __init__(self, reloj: p.RelojDelSistema):
        self.reloj = reloj

    def registrar(self, id_usuario, tabla, operacion, detalle=""):
        m.AuditoriaModelo.objects.create(usuario_id=id_usuario, tabla=tabla, operacion=operacion,
                                         detalle=detalle[:1000], fecha_hora=self.reloj.ahora())

    def listar(self, limite: int = 200) -> list[RegistroAuditoriaEntidad]:
        qs = m.AuditoriaModelo.objects.select_related("usuario").order_by("-fecha_hora", "-id")[:limite]
        return [RegistroAuditoriaEntidad(x.id, x.usuario_id, x.tabla, x.operacion, x.detalle, x.fecha_hora,
                                         x.usuario.nombre_completo if x.usuario else "(sistema)") for x in qs]


class TransaccionORM(p.Transaccion):
    def atomico(self):
        return transaction.atomic()
