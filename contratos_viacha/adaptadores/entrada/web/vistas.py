"""Adaptador de ENTRADA web. Las vistas solo traducen HTTP <-> casos de uso:
nunca consultan el ORM ni aplican reglas de negocio (eso vive en dominio y aplicación)."""
from __future__ import annotations

import csv
import json
import re
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from contratos_viacha import composicion
from contratos_viacha.dominio import permisos
from contratos_viacha.dominio.entidades import FiltroContratos, Rol, Umbrales, Usuario
from contratos_viacha.dominio.excepciones import (CredencialesInvalidas, ErrorDeDominio, ErrorValidacion,
                                                  NoEncontrado, PermisoDenegado)
from . import formularios as f


def servicios():
    return composicion.servicios()


def actor(request) -> Usuario:
    u = request.user
    return Usuario(u.id, u.nombre_completo, u.correo, Rol(u.rol.nombre), u.activo, u.unidad_id)


def _error(request, codigo: int, mensaje: str):
    return render(request, "web/error.html", {"codigo": codigo, "mensaje": mensaje}, status=codigo)


def protegida(vista):
    """Exige sesión y traduce los errores de dominio a respuestas HTTP."""
    @wraps(vista)
    @login_required
    def envoltura(request, *args, **kwargs):
        try:
            return vista(request, *args, **kwargs)
        except PermisoDenegado as e:
            return _error(request, 403, str(e))
        except NoEncontrado as e:
            return _error(request, 404, str(e))
        except ErrorValidacion as e:
            messages.error(request, str(e))
            return redirect("web:panel")
    return envoltura


def api_protegida(vista):
    """Igual que protegida, pero responde JSON (para el chatbot)."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Su sesión expiró. Inicie sesión de nuevo."}, status=401)
        try:
            return vista(request, *args, **kwargs)
        except PermisoDenegado as e:
            return JsonResponse({"error": str(e)}, status=403)
        except NoEncontrado as e:
            return JsonResponse({"error": str(e)}, status=404)
        except ErrorValidacion as e:
            return JsonResponse({"error": str(e)}, status=400)
    return envoltura


def solo_admin(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        permisos.exigir(permisos.es_administrador(actor(request)), "Solo el administrador puede ver esta sección.")
        return vista(request, *args, **kwargs)
    return envoltura


# ------------------------------------------------------------------ acceso
def acceso(request):
    if request.user.is_authenticated:
        return redirect("web:panel")
    form = f.AccesoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            usuario = servicios().usuarios.iniciar_sesion(form.cleaned_data["correo"], form.cleaned_data["password"])
            login(request, get_user_model().objects.get(pk=usuario.id), backend="django.contrib.auth.backends.ModelBackend")
            destino = request.GET.get("next", "")
            if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
                return redirect(destino)
            return redirect("web:panel")
        except CredencialesInvalidas as e:
            form.add_error(None, str(e))
    return render(request, "web/acceso.html", {"form": form})


@require_POST
def salir(request):
    logout(request)
    return redirect("web:acceso")


@require_GET
def salud(request):
    return HttpResponse("ok", content_type="text/plain")


# ------------------------------------------------------------------ panel
@protegida
def panel(request):
    datos = servicios().consultar.panel(actor(request))
    total = max(datos["total"], 1)
    orden = [("vigente", "Vigente"), ("proximo_a_vencer", "Próximo a vencer"), ("critico", "Crítico"),
             ("vencido", "Vencido"), ("renovado", "Renovado"), ("terminado", "Terminado")]
    barras = [{"clave": k, "etiqueta": e, "n": datos["conteos"][k], "pct": round(datos["conteos"][k] * 100 / total)}
              for k, e in orden]
    return render(request, "web/panel.html", {**datos, "barras": barras})


# ------------------------------------------------------------------ contratos
@protegida
def contratos_lista(request):
    s, a = servicios(), actor(request)
    form = f.FiltroForm(request.GET or None, catalogos=s.gestionar.catalogos(a))
    filtro = FiltroContratos()
    if form.is_valid():
        d = form.cleaned_data
        filtro = FiltroContratos(estado=d["estado"] or None, id_tipo=int(d["id_tipo"]) if d["id_tipo"] else None,
                                 id_contratista=int(d["id_contratista"]) if d["id_contratista"] else None,
                                 texto=d["texto"] or None)
    contratos = s.consultar.buscar(a, filtro)
    return render(request, "web/contratos_lista.html", {"form": form, "contratos": contratos})


def _formulario_contrato(request, id_contrato=None):
    s, a = servicios(), actor(request)
    permisos.exigir(permisos.puede_editar_contratos(a), "No tiene permiso para registrar o editar contratos.")
    cat = s.gestionar.catalogos(a)
    inicial = None
    if id_contrato and request.method != "POST":
        c = s.gestionar.ficha(a, id_contrato)["contrato"]
        inicial = dict(numero=c.numero, objeto=c.objeto, id_tipo=str(c.id_tipo), id_contratista=str(c.id_contratista),
                       id_responsable=str(c.id_responsable), monto=c.monto, fecha_inicio=c.fecha_inicio,
                       fecha_vencimiento=c.fecha_vencimiento)
    form = f.ContratoForm(request.POST or None, initial=inicial, catalogos=cat, con_garantia=id_contrato is None)
    if request.method == "POST" and form.is_valid():
        datos = dict(form.cleaned_data)
        for k in ("id_tipo", "id_contratista", "id_responsable"):
            datos[k] = int(datos[k])
        try:
            if id_contrato:
                c = s.gestionar.editar_contrato(a, id_contrato, datos)
                messages.success(request, f"Contrato {c.numero} actualizado.")
            else:
                c = s.gestionar.registrar_contrato(a, datos)
                messages.success(request, f"Contrato {c.numero} registrado con estado «{c.estado.etiqueta}».")
            return redirect("web:contrato_ficha", c.id)
        except ErrorValidacion as e:
            form.add_error(None, str(e))
    return render(request, "web/contrato_form.html", {"form": form, "editando": id_contrato})


@protegida
def contrato_nuevo(request):
    return _formulario_contrato(request)


@protegida
def contrato_editar(request, id_contrato):
    return _formulario_contrato(request, id_contrato)


@protegida
def contrato_ficha(request, id_contrato):
    ficha = servicios().gestionar.ficha(actor(request), id_contrato)
    c = ficha["contrato"]
    from contratos_viacha.dominio.reglas_vencimiento import estado_para_contrato
    s = servicios()
    c.estado = estado_para_contrato(c.estado, c.fecha_vencimiento, s.consultar.reloj.hoy(), s.consultar.umbrales.obtener())
    return render(request, "web/contrato_ficha.html", {**ficha, "seg_form": f.SeguimientoForm(),
                                                       "gar_form": f.GarantiaForm()})


@require_POST
@protegida
def contrato_estado(request, id_contrato):
    accion = request.POST.get("estado", "")
    c = servicios().gestionar.marcar_estado_final(actor(request), id_contrato, accion)
    messages.success(request, f"Contrato {c.numero}: estado actualizado a «{c.estado.etiqueta}».")
    return redirect("web:contrato_ficha", id_contrato)


@require_POST
@protegida
def garantia_nueva(request, id_contrato):
    form = f.GarantiaForm(request.POST)
    if form.is_valid():
        servicios().gestionar.registrar_garantia(actor(request), id_contrato, form.cleaned_data["tipo"],
                                                 form.cleaned_data["fecha_vencimiento"])
        messages.success(request, "Garantía registrada.")
    else:
        messages.error(request, "Revise los datos de la garantía.")
    return redirect("web:contrato_ficha", id_contrato)


@require_POST
@protegida
def seguimiento_nuevo(request, id_contrato):
    form = f.SeguimientoForm(request.POST)
    if form.is_valid():
        servicios().seguimiento.registrar(actor(request), id_contrato, form.cleaned_data["accion"])
        messages.success(request, "Acción registrada en el seguimiento.")
    else:
        messages.error(request, "Describa la acción realizada.")
    return redirect("web:contrato_ficha", id_contrato)


# ------------------------------------------------------------------ documentos
@require_POST
@protegida
def documento_subir(request, id_contrato):
    servicios().gestionar.ficha(actor(request), id_contrato)  # primero el permiso: lanza 403/404 si corresponde
    archivo = request.FILES.get("archivo")
    if archivo is None:
        raise ErrorValidacion("Seleccione un archivo.")
    if archivo.size > 10 * 1024 * 1024:
        raise ErrorValidacion("El archivo supera el tamaño máximo de 10 MB.")
    try:
        d = servicios().subir_documento.subir(actor(request), id_contrato, archivo.name, archivo.read())
        messages.success(request, f"Documento «{d.nombre_original}» subido.")
    except ErrorValidacion as e:
        messages.error(request, str(e))
    return redirect("web:contrato_ficha", id_contrato)


@protegida
def documento_descargar(request, id_documento):
    doc, contenido = servicios().documentos.descargar(actor(request), id_documento)
    tipos = {"pdf": "application/pdf", "txt": "text/plain; charset=utf-8",
             "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    import io
    resp = FileResponse(io.BytesIO(contenido), as_attachment=True, filename=re.sub(r'[^\w.\- ]', "_", doc.nombre_original),
                        content_type=tipos.get(doc.tipo, "application/octet-stream"))
    resp["X-Content-Type-Options"] = "nosniff"
    return resp


# ------------------------------------------------------------------ contratistas
@protegida
def contratistas(request):
    s, a = servicios(), actor(request)
    permisos.exigir(permisos.puede_editar_contratos(a), "Solo el funcionario de contrataciones o el administrador gestionan contratistas.")
    form = f.ContratistaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            c = s.gestionar.registrar_contratista(a, form.cleaned_data)
            messages.success(request, f"Contratista «{c.razon_social}» registrado.")
            return redirect("web:contratistas")
        except ErrorValidacion as e:
            form.add_error(None, str(e))
    return render(request, "web/contratistas.html", {"form": form, "lista": s.gestionar.catalogos(a)["contratistas"]})


# ------------------------------------------------------------------ alertas y reportes
@protegida
def alertas(request):
    solo = request.GET.get("pendientes") == "1"
    return render(request, "web/alertas.html", {"alertas": servicios().seguimiento.alertas(actor(request), solo), "solo": solo})


@require_POST
@protegida
def alerta_leida(request, id_alerta):
    servicios().seguimiento.marcar_alerta_leida(actor(request), id_alerta)
    return redirect("web:alertas")


def _csv_seguro(valor) -> str:
    t = str(valor)
    return "'" + t if t[:1] in ("=", "+", "-", "@") else t  # evita inyección de fórmulas en Excel


@protegida
def reportes(request):
    tipo = request.GET.get("tipo", "por_vencer")
    contratos = servicios().consultar.reporte(actor(request), tipo)
    if request.GET.get("formato") == "csv":
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="reporte_{tipo}.csv"'
        resp.write("\ufeff")
        w = csv.writer(resp)
        w.writerow(["Número", "Objeto", "Tipo", "Contratista", "Responsable", "Vencimiento", "Estado", "Monto"])
        for c in contratos:
            w.writerow([_csv_seguro(x) for x in (c.numero, c.objeto, c.tipo_nombre, c.contratista_nombre,
                                                 c.responsable_nombre, c.fecha_vencimiento.strftime("%d/%m/%Y"),
                                                 c.estado.etiqueta, c.monto)])
        return resp
    titulos = {"por_vencer": "Contratos por vencer", "vencidos": "Contratos vencidos", "todos": "Todos los contratos"}
    return render(request, "web/reportes.html", {"contratos": contratos, "tipo": tipo, "titulo": titulos.get(tipo, "Reporte"), "titulos": titulos})


# ------------------------------------------------------------------ administración
@protegida
@solo_admin
def usuarios(request):
    s, a = servicios(), actor(request)
    form = f.UsuarioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            s.usuarios.crear_usuario(a, d["nombre"], d["correo"], d["rol"], d["password"])
            messages.success(request, "Usuario creado.")
            return redirect("web:usuarios")
        except ErrorValidacion as e:
            form.add_error(None, str(e))
    return render(request, "web/usuarios.html", {"form": form, "lista": s.usuarios.listar_usuarios(a), "roles": list(Rol)})


@require_POST
@protegida
@solo_admin
def usuario_rol(request, id_usuario):
    servicios().usuarios.cambiar_rol(actor(request), id_usuario, request.POST.get("rol", ""))
    messages.success(request, "Rol actualizado.")
    return redirect("web:usuarios")


@require_POST
@protegida
@solo_admin
def usuario_activo(request, id_usuario):
    servicios().usuarios.activar(actor(request), id_usuario, request.POST.get("activo") == "1")
    messages.success(request, "Estado del usuario actualizado.")
    return redirect("web:usuarios")


@protegida
@solo_admin
def umbrales(request):
    s, a = servicios(), actor(request)
    actual = s.usuarios.obtener_umbrales(a)
    form = f.UmbralesForm(request.POST or None, initial=vars(actual) if request.method != "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            d = form.cleaned_data
            s.usuarios.configurar_umbrales(a, Umbrales(d["dias_proximo"], d["dias_critico"], d["aviso_1"], d["aviso_2"]))
            messages.success(request, "Umbrales actualizados.")
            return redirect("web:umbrales")
        except ErrorValidacion as e:
            form.add_error(None, str(e))
    return render(request, "web/umbrales.html", {"form": form})


@protegida
@solo_admin
def auditoria(request):
    return render(request, "web/auditoria.html", {"registros": servicios().usuarios.bitacora(actor(request), 300)})


# ------------------------------------------------------------------ chatbot
@require_POST
@api_protegida
def chatbot_consultar(request):
    try:
        mensaje = json.loads(request.body.decode("utf-8")).get("mensaje", "")
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Solicitud no válida."}, status=400)
    if not isinstance(mensaje, str):
        return JsonResponse({"error": "Solicitud no válida."}, status=400)
    r = servicios().chatbot.consultar(actor(request), mensaje)
    return JsonResponse(r)


@require_POST
@api_protegida
def chatbot_subir(request):
    a, s = actor(request), servicios()
    archivo, numero = request.FILES.get("archivo"), (request.POST.get("numero") or "").strip()
    if archivo is None or not numero:
        raise ErrorValidacion("Indique el número del contrato y seleccione un archivo.")
    if archivo.size > 10 * 1024 * 1024:
        raise ErrorValidacion("El archivo supera el tamaño máximo de 10 MB.")
    candidatos = [c for c in s.consultar.buscar(a, FiltroContratos(texto=numero)) if c.numero.lower() == numero.lower()]
    if not candidatos:
        raise NoEncontrado(f"No encontré el contrato {numero} entre los que usted puede ver.")
    d = s.subir_documento.subir(a, candidatos[0].id, archivo.name, archivo.read())
    return JsonResponse({"ok": True, "texto": f"Documento «{d.nombre_original}» adjuntado al contrato {d.contrato_numero}. "
                                              f"Ya puedes preguntarme sobre su contenido."})
