"""Pruebas de INTEGRACIÓN: vistas Django + casos de uso + repositorios sobre PostgreSQL real."""
import io
import json
import zipfile
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction

from contratos_viacha.adaptadores.salida.persistencia import models as m
from contratos_viacha.dominio.excepciones import ErrorValidacion
from contratos_viacha.pruebas.conftest import CLAVE, HOY

pytestmark = pytest.mark.django_db


def post_contrato(c, mundo, numero, ini, venc, **extra):
    datos = {"numero": numero, "objeto": "Obra de prueba", "id_tipo": 1, "id_contratista": mundo.contratista.id,
             "id_responsable": mundo.resp1.id, "monto": "2500.50", "fecha_inicio": ini, "fecha_vencimiento": venc}
    datos.update(extra)
    return c.post("/contratos/nuevo/", datos)


# ------------------------------------------------------------------ acceso (CP-01, CP-02)
def test_cp01_login_valido_redirige_al_panel(mundo, client):
    r = client.post("/acceso/", {"correo": mundo.func.correo, "password": CLAVE})
    assert r.status_code == 302 and r["Location"] == "/"
    assert client.get("/").status_code == 200


def test_cp02_login_invalido_muestra_mensaje_claro(mundo, client):
    r = client.post("/acceso/", {"correo": mundo.func.correo, "password": "incorrecta"})
    assert r.status_code == 200 and "Usuario o contraseña incorrectos" in r.content.decode()
    assert client.get("/").status_code == 302  # sigue sin sesión


def test_sin_sesion_redirige_al_acceso(client, db):
    r = client.get("/contratos/")
    assert r.status_code == 302 and r["Location"].startswith("/acceso/")


def test_no_se_sigue_una_redireccion_a_otro_sitio(mundo, client):
    r = client.post("/acceso/?next=https://sitio-malicioso.example/", {"correo": mundo.func.correo, "password": CLAVE})
    assert r.status_code == 302 and "malicioso" not in r["Location"]


def test_cerrar_sesion_exige_post(mundo, entrar):
    c = entrar(mundo.func)
    assert c.get("/salir/").status_code == 405
    assert c.post("/salir/").status_code == 302
    assert c.get("/").status_code == 302


def test_usuario_inactivo_no_entra(mundo, client):
    mundo.svc.usuarios.activar(mundo.admin, mundo.resp1.id, False)
    r = client.post("/acceso/", {"correo": mundo.resp1.correo, "password": CLAVE})
    assert r.status_code == 200 and client.get("/").status_code == 302


# ------------------------------------------------------------------ contratos (CP-03, CP-04, CP-05, CP-12)
def test_cp03_registrar_contrato_calcula_el_estado(mundo, entrar):
    c = entrar(mundo.func)
    r = post_contrato(c, mundo, "100/2026", "2026-06-01", (HOY + timedelta(days=7)).isoformat())
    assert r.status_code == 302
    fila = m.ContratoModelo.objects.get(numero="100/2026")
    assert fila.estado == "critico" and str(fila.monto) == "2500.50"


def test_registrar_contrato_con_garantia_en_la_misma_operacion(mundo, entrar):
    c = entrar(mundo.func)
    post_contrato(c, mundo, "101/2026", "2026-06-01", "2027-06-01", garantia_tipo="boleta", garantia_vencimiento="2027-06-15")
    assert m.GarantiaModelo.objects.filter(contrato__numero="101/2026", tipo="boleta").count() == 1


def test_cp04_fechas_incoherentes_no_se_guardan(mundo, entrar):
    r = post_contrato(entrar(mundo.func), mundo, "102/2026", "2026-12-31", "2026-01-01")
    assert r.status_code == 200 and "anterior" in r.content.decode()
    assert not m.ContratoModelo.objects.filter(numero="102/2026").exists()


def test_cp05_numero_repetido_se_rechaza(mundo, entrar):
    mundo.contrato(100, "103/2026")
    r = post_contrato(entrar(mundo.func), mundo, "103/2026", "2026-06-01", "2027-06-01")
    assert r.status_code == 200 and "Ya existe" in r.content.decode()
    assert m.ContratoModelo.objects.filter(numero="103/2026").count() == 1


def test_cp12_editar_deja_registro_en_la_bitacora(mundo, entrar):
    c = mundo.contrato(100, "104/2026")
    cl = entrar(mundo.func)
    r = cl.post(f"/contratos/{c.id}/editar/", {"numero": "104/2026", "objeto": "Objeto modificado", "id_tipo": 1,
                "id_contratista": mundo.contratista.id, "id_responsable": mundo.resp1.id, "monto": "1",
                "fecha_inicio": c.fecha_inicio.isoformat(), "fecha_vencimiento": c.fecha_vencimiento.isoformat()})
    assert r.status_code == 302
    reg = m.AuditoriaModelo.objects.filter(tabla="contrato", operacion="UPDATE").latest("id")
    assert reg.usuario_id == mundo.func.id and "objeto" in reg.detalle and reg.fecha_hora


def test_filtros_de_la_lista(mundo, entrar):
    mundo.contrato(3, "110/2026"); mundo.contrato(300, "111/2026")
    c = entrar(mundo.func)
    html = c.get("/contratos/?estado=critico").content.decode()
    assert "110/2026" in html and "111/2026" not in html
    assert "111/2026" in c.get("/contratos/?texto=111").content.decode()


# ------------------------------------------------------------------ permisos por rol (CP-11)
def test_cp11_responsable_no_abre_un_contrato_ajeno(mundo, entrar):
    ajeno = mundo.contrato(10, "120/2026", responsable=mundo.resp2)
    propio = mundo.contrato(10, "121/2026", responsable=mundo.resp1)
    c = entrar(mundo.resp1)
    assert c.get(f"/contratos/{ajeno.id}/").status_code == 403
    assert c.get(f"/contratos/{propio.id}/").status_code == 200
    assert "120/2026" not in c.get("/contratos/").content.decode()
    assert "120/2026" not in c.get("/").content.decode()


@pytest.mark.parametrize("quien,ruta,codigo", [
    ("resp1", "/contratos/nuevo/", 403), ("autoridad", "/contratos/nuevo/", 403), ("resp1", "/reportes/", 403),
    ("resp1", "/contratistas/", 403), ("func", "/administracion/usuarios/", 403), ("autoridad", "/administracion/auditoria/", 403),
    ("resp1", "/administracion/umbrales/", 403), ("admin", "/administracion/usuarios/", 200), ("admin", "/administracion/auditoria/", 200),
    ("autoridad", "/reportes/", 200), ("func", "/contratos/nuevo/", 200), ("func", "/reportes/?tipo=todos&formato=csv", 200)])
def test_acceso_por_rol(mundo, entrar, quien, ruta, codigo):
    assert entrar(getattr(mundo, quien)).get(ruta).status_code == codigo


def test_el_menu_solo_muestra_lo_permitido(mundo, entrar):
    html = entrar(mundo.resp1).get("/").content.decode()
    assert "Bitácora" not in html and "Reportes" not in html and "Usuarios" not in html
    html = entrar(mundo.admin).get("/").content.decode()
    assert "Bitácora" in html and "Usuarios" in html


def test_un_usuario_no_puede_cambiar_roles_si_no_es_admin(mundo, entrar):
    r = entrar(mundo.func).post(f"/administracion/usuarios/{mundo.resp1.id}/rol/", {"rol": "administrador"})
    assert r.status_code == 403
    assert m.UsuarioModelo.objects.get(pk=mundo.resp1.id).rol.nombre == "responsable"


# ------------------------------------------------------------------ seguridad
def test_las_contrasenas_se_guardan_con_hash(mundo):
    guardada = m.UsuarioModelo.objects.get(pk=mundo.func.id).password
    assert guardada != CLAVE and guardada.startswith("pbkdf2_") and CLAVE not in guardada


def test_inyeccion_sql_en_la_busqueda_no_devuelve_ni_rompe_nada(mundo, entrar):
    contrato = mundo.contrato(10, "130/2026")
    c = entrar(mundo.func)
    fila = f'href="/contratos/{contrato.id}/"'  # la fila del contrato en la tabla de resultados
    assert fila in c.get("/contratos/").content.decode()  # sin ataque, el contrato sí aparece
    for ataque in ("' OR '1'='1", "'; DROP TABLE contrato; --", "130/2026' UNION SELECT password_hash FROM usuario --"):
        r = c.get("/contratos/", {"texto": ataque})
        assert r.status_code == 200 and fila not in r.content.decode()  # el ataque no devuelve filas de más
        assert "pbkdf2_" not in r.content.decode()
    assert m.ContratoModelo.objects.filter(numero="130/2026").exists()


def test_xss_el_contenido_del_usuario_se_escapa(mundo, entrar):
    c = mundo.contrato(10, "131/2026", objeto="<script>alert('xss')</script> Obra")
    mundo.svc.seguimiento.registrar(mundo.resp1, c.id, "<img src=x onerror=alert(1)>")
    cl = entrar(mundo.func)
    for ruta in ("/contratos/", f"/contratos/{c.id}/", "/"):
        html = cl.get(ruta).content.decode()
        assert "<script>alert('xss')</script>" not in html and "<img src=x onerror" not in html
    assert "&lt;script&gt;" in cl.get(f"/contratos/{c.id}/").content.decode()


def test_csrf_se_exige_en_los_formularios(mundo):
    from django.test import Client
    c = Client(enforce_csrf_checks=True)
    assert c.post("/acceso/", {"correo": mundo.func.correo, "password": CLAVE}).status_code == 403


def test_csrf_se_exige_tambien_en_el_chatbot(mundo, entrar):
    from django.test import Client
    cl = Client(enforce_csrf_checks=True)
    r = cl.get("/acceso/")
    token = r.cookies["csrftoken"].value
    cl.post("/acceso/", {"correo": mundo.func.correo, "password": CLAVE, "csrfmiddlewaretoken": token})
    token = cl.cookies["csrftoken"].value  # Django rota el token al iniciar sesión
    assert cl.post("/chatbot/consultar/", data=json.dumps({"mensaje": "ayuda"}), content_type="application/json").status_code == 403
    ok = cl.post("/chatbot/consultar/", data=json.dumps({"mensaje": "ayuda"}), content_type="application/json", HTTP_X_CSRFTOKEN=token)
    assert ok.status_code == 200


def test_cabeceras_y_cookies_de_sesion_seguras(mundo, entrar):
    c = entrar(mundo.func)
    r = c.get("/")
    assert r["X-Frame-Options"] == "DENY" and r["X-Content-Type-Options"] == "nosniff"
    ck = c.cookies["sessionid"]
    assert ck["httponly"] and ck["samesite"] == "Lax"
    from django.conf import settings
    assert settings.SESSION_COOKIE_AGE == 1800


def test_la_base_de_datos_misma_protege_la_integridad(mundo):
    base = dict(objeto="x", tipo_id=1, contratista_id=mundo.contratista.id, responsable_id=mundo.resp1.id)
    with pytest.raises(IntegrityError), transaction.atomic():
        m.ContratoModelo.objects.create(numero="140/2026", fecha_inicio=HOY, fecha_vencimiento=HOY - timedelta(days=1), monto=1, **base)
    with pytest.raises(IntegrityError), transaction.atomic():
        m.ContratoModelo.objects.create(numero="141/2026", fecha_inicio=HOY, fecha_vencimiento=HOY, monto=-5, **base)
    m.ContratoModelo.objects.create(numero="142/2026", fecha_inicio=HOY, fecha_vencimiento=HOY, monto=1, **base)
    with pytest.raises(IntegrityError), transaction.atomic():
        m.ContratoModelo.objects.create(numero="142/2026", fecha_inicio=HOY, fecha_vencimiento=HOY, monto=1, **base)


def test_la_transaccion_deshace_todo_si_algo_falla(mundo):
    """Registrar un contrato con una garantía inválida no deja el contrato a medias."""
    with pytest.raises(ErrorValidacion):
        mundo.contrato(100, "150/2026", garantia_tipo="cheque", garantia_vencimiento=HOY)
    assert not m.ContratoModelo.objects.filter(numero="150/2026").exists()


def test_el_csv_neutraliza_formulas(mundo, entrar):
    mundo.contrato(10, "151/2026", objeto="=HYPERLINK(\"http://x\")")
    csv = entrar(mundo.func).get("/reportes/?tipo=todos&formato=csv").content.decode("utf-8-sig")
    assert "'=HYPERLINK" in csv and ",=HYPERLINK" not in csv


# ------------------------------------------------------------------ documentos
def pdf_valido():
    return b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


def docx_valido(texto="Contenido del acta"):
    from docx import Document
    d = Document(); d.add_paragraph(texto)
    b = io.BytesIO(); d.save(b)
    return b.getvalue()


def subir(c, id_contrato, nombre, contenido):
    from django.core.files.uploadedfile import SimpleUploadedFile
    return c.post(f"/contratos/{id_contrato}/documento/", {"archivo": SimpleUploadedFile(nombre, contenido)}, follow=True)


def test_subir_docx_valido_extrae_texto_y_guarda_con_nombre_aleatorio(mundo, entrar):
    c = mundo.contrato(100, "160/2026")
    r = subir(entrar(mundo.func), c.id, "acta original.docx", docx_valido("La multa es del 3 por ciento."))
    assert "subido" in r.content.decode()
    d = m.DocumentoModelo.objects.get(contrato_id=c.id)
    assert "multa" in d.texto_extraido and d.nombre_archivo != "acta original.docx"
    assert (mundo.svc.carpeta_docs / d.nombre_archivo).exists()
    assert not (mundo.svc.carpeta_docs / "acta original.docx").exists()


@pytest.mark.parametrize("nombre,contenido", [("virus.exe", b"MZ\x90\x00"), ("falso.pdf", b"<?php system($_GET[1]); ?>"),
                                              ("falso.docx", b"no es un zip"), ("macro.docm", b"PK\x03\x04"), ("vacio.txt", b"")])
def test_archivos_peligrosos_o_falsos_se_rechazan(mundo, entrar, nombre, contenido):
    c = mundo.contrato(100, "161/2026")
    subir(entrar(mundo.func), c.id, nombre, contenido)
    assert m.DocumentoModelo.objects.count() == 0
    assert not list(mundo.svc.carpeta_docs.glob("*"))


def test_docx_falso_con_estructura_de_zip_incorrecta_se_rechaza(mundo, entrar):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("otro.txt", "no soy un docx")
    c = mundo.contrato(100, "162/2026")
    subir(entrar(mundo.func), c.id, "disfrazado.docx", b.getvalue())
    assert m.DocumentoModelo.objects.count() == 0


def test_documento_de_contrato_ajeno_no_se_sube_ni_se_descarga(mundo, entrar):
    c = mundo.contrato(100, "163/2026", responsable=mundo.resp2)
    assert subir(entrar(mundo.func), c.id, "a.txt", b"texto").status_code == 200
    d = m.DocumentoModelo.objects.get(contrato_id=c.id)
    assert entrar(mundo.resp1).get(f"/documentos/{d.id}/descargar/").status_code == 403
    assert entrar(mundo.resp1).post(f"/contratos/{c.id}/documento/", {}).status_code == 403
    r = entrar(mundo.resp2).get(f"/documentos/{d.id}/descargar/")
    assert r.status_code == 200 and "attachment" in r["Content-Disposition"] and r["X-Content-Type-Options"] == "nosniff"
    assert b"".join(r.streaming_content) == b"texto"


# ------------------------------------------------------------------ chatbot por HTTP
def test_el_chatbot_exige_sesion(mundo, client):
    r = client.post("/chatbot/consultar/", data=json.dumps({"mensaje": "ayuda"}), content_type="application/json")
    assert r.status_code == 401


def test_cp09_el_chatbot_responde_con_datos_reales(mundo, entrar):
    mundo.contrato(3, "170/2026")
    r = entrar(mundo.resp1).post("/chatbot/consultar/", data=json.dumps({"mensaje": "¿Qué vence esta semana?"}), content_type="application/json")
    d = r.json()
    assert r.status_code == 200 and "170/2026" in d["texto"] and d["adaptador"] == "plantillas"
    assert m.ConsultaChatbotModelo.objects.filter(usuario_id=mundo.resp1.id, intencion="vencimientos_proximos").count() == 1


def test_el_chatbot_rechaza_solicitudes_mal_formadas(mundo, entrar):
    c = entrar(mundo.func)
    assert c.post("/chatbot/consultar/", data="no es json", content_type="application/json").status_code == 400
    assert c.post("/chatbot/consultar/", data=json.dumps({"mensaje": ["x"]}), content_type="application/json").status_code == 400
    assert c.get("/chatbot/consultar/").status_code == 405


def test_subir_un_documento_desde_el_chat_y_preguntar_por_su_contenido(mundo, entrar):
    from django.core.files.uploadedfile import SimpleUploadedFile
    mundo.contrato(100, "171/2026")
    c = entrar(mundo.func)
    r = c.post("/chatbot/subir/", {"numero": "171/2026", "archivo": SimpleUploadedFile("clausulas.txt", b"La penalidad por retraso es del 4 por ciento.")})
    assert r.status_code == 200 and r.json()["ok"]
    r = c.post("/chatbot/consultar/", data=json.dumps({"mensaje": "¿Qué dice el contrato 171/2026 sobre la penalidad?"}), content_type="application/json")
    assert "4 por ciento" in r.json()["texto"] and "clausulas.txt" in r.json()["texto"]


def test_subida_desde_el_chat_respeta_permisos_y_numero(mundo, entrar):
    from django.core.files.uploadedfile import SimpleUploadedFile
    mundo.contrato(100, "172/2026", responsable=mundo.resp2)
    f = lambda: SimpleUploadedFile("a.txt", b"hola")
    c = entrar(mundo.resp1)
    assert c.post("/chatbot/subir/", {"numero": "172/2026", "archivo": f()}).status_code == 404  # no lo ve: ni siquiera sabe que existe
    assert c.post("/chatbot/subir/", {"numero": "999/2026", "archivo": f()}).status_code == 404
    assert c.post("/chatbot/subir/", {"archivo": f()}).status_code == 400
    assert m.DocumentoModelo.objects.count() == 0


# ------------------------------------------------------------------ motor y comandos
def test_el_comando_de_revision_diaria_persiste_las_alertas_y_es_idempotente(mundo):
    mundo.contrato(5, "180/2026"); mundo.contrato(-2, "181/2026"); mundo.contrato(200, "182/2026")
    call_command("ejecutar_revision_diaria")
    niveles = set(m.AlertaModelo.objects.values_list("nivel", flat=True))
    assert niveles == {"critico", "vencido"} and m.AlertaModelo.objects.count() == 2
    assert m.ContratoModelo.objects.get(numero="181/2026").estado == "vencido"
    call_command("ejecutar_revision_diaria")
    assert m.AlertaModelo.objects.count() == 2
    assert len(mundo.svc.revision.notificador.enviados) == 2  # el correo simulado recibió ambos
    assert m.AlertaModelo.objects.filter(canal="correo").count() == 2


def test_el_motor_avanza_con_el_reloj_falso(mundo):
    mundo.contrato(31, "183/2026")
    call_command("ejecutar_revision_diaria")
    assert m.AlertaModelo.objects.count() == 0
    mundo.svc.revision.reloj.avanzar(1)  # ahora faltan 30 días
    call_command("ejecutar_revision_diaria")
    assert m.AlertaModelo.objects.get().nivel == "aviso_30"


def test_bandeja_de_alertas_y_marcar_leida(mundo, entrar):
    mundo.contrato(5, "184/2026", responsable=mundo.resp2)
    call_command("ejecutar_revision_diaria")
    a = m.AlertaModelo.objects.get()
    assert "184/2026" not in entrar(mundo.resp1).get("/alertas/").content.decode()
    assert entrar(mundo.resp1).post(f"/alertas/{a.id}/leida/").status_code == 403
    assert entrar(mundo.resp2).post(f"/alertas/{a.id}/leida/").status_code == 302
    assert m.AlertaModelo.objects.get().leida


def test_el_panel_muestra_el_mapa_de_riesgo(mundo, entrar):
    mundo.contrato(-3, "190/2026"); mundo.contrato(4, "191/2026"); mundo.contrato(20, "192/2026"); mundo.contrato(400, "193/2026")
    html = entrar(mundo.func).get("/").content.decode()
    for texto in ("190/2026", "191/2026", "192/2026", "Vencido", "Crítico", "Próximo a vencer"):
        assert texto in html
    assert "193/2026" not in html  # un contrato vigente no ocupa lugar en el mapa de riesgo


def test_ficha_con_garantias_alertas_y_seguimiento(mundo, entrar):
    c = mundo.contrato(5, "194/2026", garantia_tipo="poliza", garantia_vencimiento=HOY + timedelta(days=9))
    call_command("ejecutar_revision_diaria")
    mundo.svc.seguimiento.registrar(mundo.resp1, c.id, "Se hizo una llamada")
    html = entrar(mundo.resp1).get(f"/contratos/{c.id}/").content.decode()
    assert "Poliza" in html or "Póliza" in html or "poliza" in html.lower()
    assert "Crítico" in html and "Se hizo una llamada" in html


def test_administracion_de_usuarios_y_umbrales_por_la_web(mundo, entrar):
    c = entrar(mundo.admin)
    r = c.post("/administracion/usuarios/", {"nombre": "Nuevo Usuario", "correo": "nuevo@prueba.test", "rol": "responsable", "password": "otra-clave-1"})
    assert r.status_code == 302 and m.UsuarioModelo.objects.filter(correo="nuevo@prueba.test").exists()
    r = c.post("/administracion/umbrales/", {"dias_proximo": 45, "dias_critico": 10, "aviso_1": 45, "aviso_2": 20})
    assert r.status_code == 302 and m.UmbralModelo.objects.get().dias_proximo == 45
    r = c.post("/administracion/umbrales/", {"dias_proximo": 5, "dias_critico": 10, "aviso_1": 4, "aviso_2": 20})
    assert r.status_code == 200 and m.UmbralModelo.objects.get().dias_proximo == 45
    assert "Bitácora" in c.get("/administracion/auditoria/").content.decode()


# ------------------------------------------------------------------ datos de demostración
def test_los_datos_de_demostracion_cubren_todos_los_estados(db, tmp_path, monkeypatch):
    from django.test import override_settings
    with override_settings(DOCUMENTOS_DIR=tmp_path):
        call_command("cargar_datos_demo")
    estados = set(m.ContratoModelo.objects.values_list("estado", flat=True))
    assert m.ContratoModelo.objects.count() == 25 and m.DocumentoModelo.objects.count() == 2
    assert {"vencido", "critico", "proximo_a_vencer", "vigente", "renovado", "terminado"} <= estados
    assert m.UsuarioModelo.objects.filter(correo__endswith="@viacha.test").count() == 5
    assert all(o.startswith("[EJEMPLO]") for o in m.ContratoModelo.objects.values_list("objeto", flat=True))
