"""Pruebas de los CASOS DE USO con repositorios en memoria, reloj falso y correo simulado.
No hay base de datos ni servidor. Cubre CP-04 a CP-14 del plan de pruebas."""
import pytest

from contratos_viacha.dominio.entidades import EstadoContrato, FiltroContratos, Rol, Umbrales
from contratos_viacha.dominio.excepciones import (CredencialesInvalidas, ErrorValidacion, NoEncontrado,
                                                  PermisoDenegado)
from contratos_viacha.pruebas.dobles import Entorno, ModeloFalso


@pytest.fixture
def e():
    return Entorno()


# ------------------------------------------------------------ gestión de contratos
def test_registrar_contrato_calcula_estado_y_audita(e):
    c = e.contrato(7)
    assert c.estado == EstadoContrato.CRITICO
    assert any(a.tabla == "contrato" and a.operacion == "INSERT" for a in e.auditoria.datos)


def test_cp04_fechas_incoherentes_se_rechazan(e):
    with pytest.raises(ErrorValidacion):
        e.contrato(10, fecha_inicio=e.reloj.hoy().replace(year=2030))


def test_cp05_numero_repetido_se_rechaza(e):
    e.contrato(40, numero="050/2026")
    with pytest.raises(ErrorValidacion, match="Ya existe"):
        e.contrato(50, numero="050/2026")


def test_contratista_o_responsable_inexistentes_se_rechazan(e):
    with pytest.raises(ErrorValidacion):
        e.contrato(10, id_contratista=999)
    with pytest.raises(ErrorValidacion):
        e.contrato(10, id_responsable=999)


def test_monto_con_coma_decimal_y_texto_invalido(e):
    assert e.contrato(100, monto="1500,50").monto == pytest.approx(1500.50)
    with pytest.raises(ErrorValidacion):
        e.contrato(100, monto="abc")


def test_solo_funcionario_o_admin_registran(e):
    for u in (e.resp1, e.autoridad):
        with pytest.raises(PermisoDenegado):
            e.gestionar.registrar_contrato(u, {})


def test_cp12_editar_deja_registro_en_la_bitacora(e):
    c = e.contrato(100)
    e.gestionar.editar_contrato(e.funcionario, c.id, dict(numero=c.numero, objeto="Objeto nuevo", id_tipo=1,
                                id_contratista=e.contratista.id, id_responsable=e.resp1.id, monto=5,
                                fecha_inicio=c.fecha_inicio, fecha_vencimiento=c.fecha_vencimiento))
    reg = [a for a in e.auditoria.datos if a.operacion == "UPDATE" and a.tabla == "contrato"]
    assert reg and reg[-1].id_usuario == e.funcionario.id and "objeto" in reg[-1].detalle


def test_editar_recalcula_el_estado(e):
    c = e.contrato(100)
    datos = dict(numero=c.numero, objeto=c.objeto, id_tipo=1, id_contratista=e.contratista.id, id_responsable=e.resp1.id,
                 monto=1, fecha_inicio=c.fecha_inicio, fecha_vencimiento=e.reloj.hoy().replace(day=12))
    assert e.gestionar.editar_contrato(e.funcionario, c.id, datos).estado == EstadoContrato.CRITICO


def test_marcar_renovado_y_reabrir(e):
    c = e.contrato(3)
    assert e.gestionar.marcar_estado_final(e.funcionario, c.id, "renovado").estado == EstadoContrato.RENOVADO
    assert e.gestionar.marcar_estado_final(e.funcionario, c.id, "reabrir").estado == EstadoContrato.CRITICO
    with pytest.raises(ErrorValidacion):
        e.gestionar.marcar_estado_final(e.funcionario, c.id, "borrado")


def test_nit_repetido_se_rechaza(e):
    with pytest.raises(ErrorValidacion):
        e.gestionar.registrar_contratista(e.funcionario, {"razon_social": "Otra", "nit": "123"})


def test_garantia_se_guarda_con_el_contrato(e):
    c = e.contrato(60, garantia_tipo="boleta", garantia_vencimiento=e.reloj.hoy())
    assert len(e.gestionar.ficha(e.funcionario, c.id)["garantias"]) == 1


# ------------------------------------------------------------ permisos (CP-11)
def test_cp11_responsable_no_abre_contrato_ajeno(e):
    c = e.contrato(10, responsable=e.resp2)
    with pytest.raises(PermisoDenegado):
        e.gestionar.ficha(e.resp1, c.id)
    assert e.gestionar.ficha(e.resp2, c.id)["contrato"].id == c.id


def test_busqueda_filtra_por_rol(e):
    e.contrato(10, responsable=e.resp1)
    e.contrato(20, responsable=e.resp2)
    assert len(e.consultar.buscar(e.resp1, FiltroContratos())) == 1
    assert len(e.consultar.buscar(e.funcionario, FiltroContratos())) == 2
    assert len(e.consultar.buscar(e.autoridad, FiltroContratos())) == 2


def test_busqueda_por_estado_usa_la_fecha_de_hoy(e):
    e.contrato(3)
    e.contrato(200)
    assert [c.estado for c in e.consultar.buscar(e.funcionario, FiltroContratos(estado="critico"))] == [EstadoContrato.CRITICO]


def test_reportes_solo_para_quienes_corresponde(e):
    e.contrato(10)
    assert len(e.consultar.reporte(e.autoridad, "por_vencer")) == 1
    with pytest.raises(PermisoDenegado):
        e.consultar.reporte(e.resp1, "por_vencer")
    with pytest.raises(ErrorValidacion):
        e.consultar.reporte(e.autoridad, "inventado")


def test_panel_cuenta_por_estado_y_arma_el_mapa(e):
    e.contrato(-5); e.contrato(3); e.contrato(20); e.contrato(300)
    panel = e.consultar.panel(e.funcionario)
    assert panel["conteos"]["vencido"] == 1 and panel["conteos"]["critico"] == 1
    assert panel["conteos"]["proximo_a_vencer"] == 1 and panel["conteos"]["vigente"] == 1
    assert len(panel["mapa"]) == 3 and panel["total"] == 4


# ------------------------------------------------------------ motor de vencimientos
def test_cp06_contrato_a_30_dias_genera_aviso(e):
    c = e.contrato(30)
    r = e.revision.ejecutar()
    assert r.alertas_generadas == 1 and e.alertas.datos[0].nivel == "aviso_30"
    assert e.contratos.datos[c.id].estado == EstadoContrato.PROXIMO_A_VENCER


def test_cp07_y_cp13_contrato_a_7_dias_es_critico_con_reloj_falso(e):
    """CP-13: reglas con reloj falso y repositorio en memoria, sin base de datos."""
    c = e.contrato(7)
    e.revision.ejecutar()
    assert e.contratos.datos[c.id].estado == EstadoContrato.CRITICO
    assert e.alertas.datos[0].nivel == "critico"


def test_cp08_contrato_vencido_ayer(e):
    c = e.contrato(-1)
    e.revision.ejecutar()
    assert e.contratos.datos[c.id].estado == EstadoContrato.VENCIDO and e.alertas.datos[0].nivel == "vencido"


def test_ejecutar_dos_veces_el_mismo_dia_no_duplica_alertas(e):
    e.contrato(5); e.contrato(-2); e.contrato(25)
    e.revision.ejecutar()
    n = len(e.alertas.datos)
    e.revision.ejecutar()
    assert len(e.alertas.datos) == n == 3


def test_el_critico_se_repite_cada_dia(e):
    e.contrato(5)
    e.revision.ejecutar()
    e.reloj.avanzar(1)
    e.revision.ejecutar()
    assert [a.nivel for a in e.alertas.datos] == ["critico", "critico"]


def test_si_el_motor_no_corrio_emite_el_aviso_mas_urgente(e):
    e.contrato(10)
    e.revision.ejecutar()
    assert [a.nivel for a in e.alertas.datos] == ["aviso_15"]


def test_renovado_y_terminado_no_se_vigilan(e):
    c = e.contrato(3)
    e.gestionar.marcar_estado_final(e.funcionario, c.id, "terminado")
    assert e.revision.ejecutar().contratos_revisados == 0 and not e.alertas.datos


def test_alerta_de_garantia_por_vencer(e):
    e.contrato(200, garantia_tipo="boleta", garantia_vencimiento=e.reloj.hoy().replace(day=18))
    e.revision.ejecutar()
    assert e.alertas.datos[0].nivel.startswith("garantia_") and "boleta" in e.alertas.datos[0].mensaje


def test_cp14_cambiar_el_adaptador_de_correo_no_cambia_las_alertas():
    con_correo, sin_correo = Entorno(notificador_funciona=True), Entorno(notificador_funciona=False)
    for ent in (con_correo, sin_correo):
        ent.contrato(5)
        ent.revision.ejecutar()
    assert [a.nivel for a in con_correo.alertas.datos] == [a.nivel for a in sin_correo.alertas.datos] == ["critico"]
    assert con_correo.alertas.datos[0].canal == "correo" and len(con_correo.notificador.enviados) == 1
    assert sin_correo.alertas.datos[0].canal == "sistema"  # el correo falló pero la alerta quedó registrada


def test_el_motor_cambia_con_los_umbrales_configurados(e):
    e.contrato(45)
    e.admin_usuarios.configurar_umbrales(e.admin, Umbrales(60, 15, 60, 30))
    e.revision.ejecutar()
    assert e.alertas.datos[0].nivel == "aviso_30"  # a 45 días ya cae dentro del nuevo umbral de 60


def test_alerta_marcar_leida_solo_si_se_ve_el_contrato(e):
    e.contrato(5, responsable=e.resp2)
    e.revision.ejecutar()
    with pytest.raises(PermisoDenegado):
        e.seguimiento.marcar_alerta_leida(e.resp1, e.alertas.datos[0].id)
    e.seguimiento.marcar_alerta_leida(e.resp2, e.alertas.datos[0].id)
    assert e.alertas.datos[0].leida


# ------------------------------------------------------------ seguimiento
def test_registrar_seguimiento_y_permiso(e):
    c = e.contrato(10, responsable=e.resp1)
    e.seguimiento.registrar(e.resp1, c.id, "Se llamó al contratista")
    with pytest.raises(PermisoDenegado):
        e.seguimiento.registrar(e.resp2, c.id, "intento ajeno")
    with pytest.raises(PermisoDenegado):
        e.seguimiento.registrar(e.autoridad, c.id, "la autoridad solo lee")
    with pytest.raises(ErrorValidacion):
        e.seguimiento.registrar(e.resp1, c.id, "   ")
    assert len(e.gestionar.ficha(e.resp1, c.id)["seguimientos"]) == 1


# ------------------------------------------------------------ usuarios y sesión
def test_login_valido_e_invalido_quedan_en_la_bitacora(e):
    assert e.admin_usuarios.iniciar_sesion("admin@prueba.test", "clave-segura-1").rol == Rol.ADMINISTRADOR
    with pytest.raises(CredencialesInvalidas):
        e.admin_usuarios.iniciar_sesion("admin@prueba.test", "mala")
    with pytest.raises(CredencialesInvalidas):
        e.admin_usuarios.iniciar_sesion("noexiste@prueba.test", "x")
    ops = [a.operacion for a in e.auditoria.datos]
    assert ops.count("LOGIN") == 1 and ops.count("LOGIN_FALLIDO") == 2


def test_usuario_inactivo_no_inicia_sesion(e):
    e.admin_usuarios.activar(e.admin, e.resp1.id, False)
    with pytest.raises(CredencialesInvalidas):
        e.admin_usuarios.iniciar_sesion("responsableuno@prueba.test", "clave-segura-1")


def test_solo_el_administrador_gestiona_usuarios(e):
    with pytest.raises(PermisoDenegado):
        e.admin_usuarios.crear_usuario(e.funcionario, "X", "x@y.test", "funcionario", "12345678")
    with pytest.raises(PermisoDenegado):
        e.admin_usuarios.listar_usuarios(e.resp1)
    with pytest.raises(PermisoDenegado):
        e.admin_usuarios.bitacora(e.autoridad)
    with pytest.raises(PermisoDenegado):
        e.admin_usuarios.configurar_umbrales(e.funcionario, Umbrales())


@pytest.mark.parametrize("nombre,correo,rol,clave", [("", "a@b.test", "funcionario", "12345678"), ("N", "malcorreo", "funcionario", "12345678"),
                                                      ("N", "a@b.test", "superuser", "12345678"), ("N", "a@b.test", "funcionario", "corta")])
def test_crear_usuario_valida_datos(e, nombre, correo, rol, clave):
    with pytest.raises(ErrorValidacion):
        e.admin_usuarios.crear_usuario(e.admin, nombre, correo, rol, clave)


def test_no_puede_cambiarse_su_propio_rol_ni_duplicar_correos(e):
    with pytest.raises(ErrorValidacion):
        e.admin_usuarios.cambiar_rol(e.admin, e.admin.id, "funcionario")
    with pytest.raises(ErrorValidacion):
        e.admin_usuarios.crear_usuario(e.admin, "Otro", "admin@prueba.test", "funcionario", "12345678")
    assert e.admin_usuarios.cambiar_rol(e.admin, e.resp1.id, "autoridad").rol == Rol.AUTORIDAD


# ------------------------------------------------------------ documentos
def test_subir_txt_guarda_con_nombre_aleatorio_y_extrae_texto(e):
    c = e.contrato(100)
    d = e.subir.subir(e.funcionario, c.id, "multas.txt", "La multa es del 5 por ciento.".encode())
    assert d.nombre_archivo != "multas.txt" and d.nombre_archivo.endswith(".txt") and len(d.nombre_archivo) == 36
    assert d.nombre_archivo in e.almacen.archivos and "multa" in d.texto_extraido
    assert any(a.tabla == "documento" for a in e.auditoria.datos)


@pytest.mark.parametrize("nombre,contenido,mensaje", [
    ("virus.exe", b"MZ....", "no permitido"), ("script.php", b"<?php", "no permitido"), ("sin_extension", b"hola", "no permitido"),
    ("falso.pdf", b"esto no es un pdf", "PDF válido"), ("falso.docx", b"esto no es un zip", "DOCX válido"),
    ("vacio.txt", b"", "vacío"), ("binario.txt", b"abc\x00def", "no es válido")])
def test_documentos_invalidos_se_rechazan(e, nombre, contenido, mensaje):
    c = e.contrato(100)
    with pytest.raises(ErrorValidacion, match=mensaje):
        e.subir.subir(e.funcionario, c.id, nombre, contenido)
    assert not e.almacen.archivos


def test_archivo_mayor_a_10_mb_se_rechaza(e):
    c = e.contrato(100)
    with pytest.raises(ErrorValidacion, match="10 MB"):
        e.subir.subir(e.funcionario, c.id, "grande.txt", b"a" * (10 * 1024 * 1024 + 1))


def test_nombre_con_ruta_se_sanea_y_no_se_usa_en_disco(e):
    c = e.contrato(100)
    d = e.subir.subir(e.funcionario, c.id, "../../etc/passwd.txt", b"contenido")
    assert d.nombre_original == "passwd.txt" and "/" not in d.nombre_archivo and ".." not in d.nombre_archivo


def test_el_documento_hereda_el_permiso_del_contrato(e):
    c = e.contrato(100, responsable=e.resp2)
    d = e.subir.subir(e.funcionario, c.id, "multas.txt", b"La multa es del 5 por ciento.")
    with pytest.raises(PermisoDenegado):
        e.subir.subir(e.resp1, c.id, "otro.txt", b"x")
    with pytest.raises(PermisoDenegado):
        e.docs.listar(e.resp1, c.id)
    with pytest.raises(PermisoDenegado):
        e.docs.descargar(e.resp1, d.id)
    assert e.docs.buscar_fragmentos(e.resp1, "multa") == []
    assert e.docs.buscar_fragmentos(e.resp2, "multa")[0]["documento"] == "multas.txt"
    assert e.docs.descargar(e.resp2, d.id)[1] == b"La multa es del 5 por ciento."


def test_busqueda_devuelve_el_fragmento_correcto(e):
    c = e.contrato(100)
    e.subir.subir(e.funcionario, c.id, "c.txt", b"CLAUSULA UNO. El plazo es de 90 dias.\nCLAUSULA DOS. La multa por mora es del 2 por ciento.\nCLAUSULA TRES. Fin.")
    f = e.docs.buscar_fragmentos(e.funcionario, "¿qué multa hay por mora?")
    assert "multa por mora" in f[0]["fragmento"]
    assert e.docs.buscar_fragmentos(e.funcionario, "xyzzy inexistente") == []


# ------------------------------------------------------------ chatbot
def _chat(e, usuario, texto):
    return e.chatbot.consultar(usuario, texto)


def test_cp09_que_vence_esta_semana(e):
    e.contrato(3, numero="010/2026"); e.contrato(20, numero="011/2026")
    r = _chat(e, e.resp1, "¿Qué vence esta semana?")
    assert r["intencion"] == "vencimientos_proximos" and "010/2026" in r["texto"] and "011/2026" not in r["texto"]


def test_cp10_consulta_ambigua_pide_el_numero(e):
    r = _chat(e, e.resp1, "¿Cómo va el contrato?")
    assert r["aclaracion"] and "número" in r["texto"]


def test_estado_de_contrato_acepta_numero_sin_ceros(e):
    e.contrato(10, numero="045/2026")
    r = _chat(e, e.resp1, "¿Cómo está el contrato 45/2026?")
    assert "045/2026" in r["texto"] and "Crítico" not in r["texto"] and "Próximo a vencer" in r["texto"]


def test_contrato_inexistente_y_ajeno(e):
    e.contrato(10, numero="020/2026", responsable=e.resp2)
    assert "No encontré" in _chat(e, e.resp1, "estado del contrato 999/2026")["texto"]
    assert "No tienes acceso" in _chat(e, e.resp1, "¿Cómo está el contrato 020/2026?")["texto"]
    assert "020/2026" in _chat(e, e.funcionario, "¿Cómo está el contrato 020/2026?")["texto"]


def test_vencidos_garantias_responsable_e_historial(e):
    c = e.contrato(-4, numero="030/2026", garantia_tipo="boleta", garantia_vencimiento=e.reloj.hoy().replace(day=20))
    e.seguimiento.registrar(e.resp1, c.id, "Se envió nota de aviso")
    assert "030/2026" in _chat(e, e.funcionario, "¿Hay contratos vencidos?")["texto"]
    assert "030/2026" in _chat(e, e.funcionario, "¿Qué boletas vencen este mes?")["texto"]
    assert "Responsable Uno" in _chat(e, e.funcionario, "¿Quién lleva el contrato 030/2026?")["texto"]
    assert "Se envió nota" in _chat(e, e.funcionario, "¿Qué se hizo con el contrato 030/2026?")["texto"]


def test_ayuda_y_mensaje_vacio_o_desconocido(e):
    assert _chat(e, e.resp1, "ayuda")["intencion"] == "ayuda"
    assert _chat(e, e.resp1, "   ")["aclaracion"]
    r = _chat(e, e.resp1, "blah blah blah")
    assert r["intencion"] == "desconocida" and r["aclaracion"]


def test_el_modelo_solo_redacta_y_se_registra_que_adaptador_respondio():
    modelo = ModeloFalso("Hay un contrato por vencer pronto.")
    e = Entorno(modelo=modelo)
    e.contrato(3, numero="040/2026")
    r = _chat(e, e.resp1, "¿Qué vence esta semana?")
    assert r["texto"] == "Hay un contrato por vencer pronto." and r["adaptador"] == "modelo-falso"
    assert "040/2026" in modelo.llamadas[0][1]  # el contexto trae los datos reales de la base
    assert e.consultas.datos[-1].adaptador == "modelo-falso"


def test_si_el_modelo_falla_el_chatbot_responde_con_plantillas():
    """Prueba del respaldo: la caída del modelo no tumba el chatbot."""
    e = Entorno(modelo=ModeloFalso(falla=True))
    e.contrato(3, numero="040/2026")
    r = _chat(e, e.resp1, "¿Qué vence esta semana?")
    assert "040/2026" in r["texto"] and r["adaptador"] == "plantillas"
    assert e.consultas.datos[-1].adaptador == "plantillas"


def test_el_modelo_no_se_usa_para_aclaraciones_ni_ayuda():
    modelo = ModeloFalso("x")
    e = Entorno(modelo=modelo)
    _chat(e, e.resp1, "¿Cómo va el contrato?")
    _chat(e, e.resp1, "ayuda")
    assert modelo.llamadas == []


def test_modelo_como_apoyo_para_clasificar_cuando_las_reglas_no_reconocen():
    modelo = ModeloFalso("vencimientos_proximos")
    e = Entorno(modelo=modelo)
    e.contrato(3, numero="040/2026")
    r = _chat(e, e.resp1, "dime lo que urge")
    assert r["intencion"] == "vencimientos_proximos"


def test_respuesta_sobre_documentos_siempre_cita_la_fuente():
    e = Entorno(modelo=ModeloFalso("La multa es del 5 por ciento."))
    c = e.contrato(100, numero="050/2026")
    e.subir.subir(e.funcionario, c.id, "multas.txt", b"La multa por mora es del 5 por ciento del monto.")
    r = _chat(e, e.funcionario, "¿Qué dice el contrato 050/2026 sobre las multas?")
    assert r["intencion"] == "consultar_documento" and "Fuente" in r["texto"] and "multas.txt" in r["texto"]
    assert r["fuentes"][0]["contrato"] == "050/2026"


def test_sin_documentos_no_se_inventa_respuesta():
    modelo = ModeloFalso("Invento algo")
    e = Entorno(modelo=modelo)
    e.contrato(100, numero="050/2026")
    r = _chat(e, e.funcionario, "¿Qué dice el contrato 050/2026 sobre las multas?")
    assert "No encontré información" in r["texto"] and modelo.llamadas == []


def test_el_chatbot_no_filtra_documentos_de_contratos_ajenos(e):
    c = e.contrato(100, numero="060/2026", responsable=e.resp2)
    e.subir.subir(e.funcionario, c.id, "secreto.txt", b"La multa es confidencial del 9 por ciento.")
    r = _chat(e, e.resp1, "¿qué dice sobre la multa?")
    assert "confidencial" not in r["texto"] and "No encontré" in r["texto"]


def test_toda_consulta_queda_registrada(e):
    _chat(e, e.resp1, "ayuda")
    assert e.consultas.datos[-1].mensaje == "ayuda" and e.consultas.datos[-1].intencion == "ayuda"
