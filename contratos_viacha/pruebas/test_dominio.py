"""Pruebas del DOMINIO: Python puro, sin base de datos, sin servidor y con fechas controladas."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from contratos_viacha.dominio import permisos
from contratos_viacha.dominio.entidades import (Contratista, Contrato, EstadoContrato, Garantia, Rol, Seguimiento,
                                                Umbrales, Usuario)
from contratos_viacha.dominio.excepciones import ErrorValidacion, PermisoDenegado
from contratos_viacha.dominio.reglas_vencimiento import (calcular_estado, dias_restantes, estado_para_contrato,
                                                         nivel_alerta_pendiente)

HOY = date(2026, 11, 10)


def venc(dias):
    return HOY + timedelta(days=dias)


@pytest.mark.parametrize("dias,esperado", [
    (365, EstadoContrato.VIGENTE), (31, EstadoContrato.VIGENTE),
    (30, EstadoContrato.PROXIMO_A_VENCER), (8, EstadoContrato.PROXIMO_A_VENCER),
    (7, EstadoContrato.CRITICO), (1, EstadoContrato.CRITICO), (0, EstadoContrato.CRITICO),
    (-1, EstadoContrato.VENCIDO), (-90, EstadoContrato.VENCIDO)])
def test_estado_en_los_valores_limite(dias, esperado):
    """Valores límite de los umbrales 30 y 7 días (caja negra: análisis de valores límite)."""
    assert calcular_estado(venc(dias), HOY) == esperado


def test_umbrales_personalizados_cambian_el_estado():
    u = Umbrales(dias_proximo=60, dias_critico=15, aviso_1=60, aviso_2=30)
    assert calcular_estado(venc(45), HOY, u) == EstadoContrato.PROXIMO_A_VENCER
    assert calcular_estado(venc(45), HOY) == EstadoContrato.VIGENTE
    assert calcular_estado(venc(15), HOY, u) == EstadoContrato.CRITICO


def test_umbrales_incoherentes_se_rechazan():
    with pytest.raises(ErrorValidacion):
        Umbrales(dias_proximo=5, dias_critico=7)
    with pytest.raises(ErrorValidacion):
        Umbrales(aviso_1=10, aviso_2=20)


def test_dias_restantes_negativo_si_vencio():
    assert dias_restantes(venc(-3), HOY) == -3 and dias_restantes(venc(12), HOY) == 12


@pytest.mark.parametrize("estado", [EstadoContrato.RENOVADO, EstadoContrato.TERMINADO])
def test_los_estados_finales_no_se_recalculan(estado):
    assert estado_para_contrato(estado, venc(-50), HOY) == estado


def test_estado_registrado_se_recalcula():
    assert estado_para_contrato(EstadoContrato.REGISTRADO, venc(3), HOY) == EstadoContrato.CRITICO


# ---- alertas (idempotencia y puesta al día) ----
def test_alerta_vencido_una_sola_vez():
    assert nivel_alerta_pendiente(EstadoContrato.VENCIDO, -1, set(), False) == "vencido"
    assert nivel_alerta_pendiente(EstadoContrato.VENCIDO, -5, {"vencido"}, False) is None


def test_alerta_critica_una_por_dia():
    assert nivel_alerta_pendiente(EstadoContrato.CRITICO, 5, set(), False) == "critico"
    assert nivel_alerta_pendiente(EstadoContrato.CRITICO, 5, {"critico"}, True) is None


def test_avisos_de_30_y_15_dias():
    assert nivel_alerta_pendiente(EstadoContrato.PROXIMO_A_VENCER, 30, set(), False) == "aviso_30"
    assert nivel_alerta_pendiente(EstadoContrato.PROXIMO_A_VENCER, 20, {"aviso_30"}, False) is None
    assert nivel_alerta_pendiente(EstadoContrato.PROXIMO_A_VENCER, 15, {"aviso_30"}, False) == "aviso_15"
    assert nivel_alerta_pendiente(EstadoContrato.PROXIMO_A_VENCER, 10, {"aviso_30", "aviso_15"}, False) is None


def test_si_el_motor_no_corrio_se_pone_al_dia_con_el_aviso_mas_urgente():
    assert nivel_alerta_pendiente(EstadoContrato.PROXIMO_A_VENCER, 10, set(), False) == "aviso_15"


def test_vigente_y_finales_no_generan_alerta():
    assert nivel_alerta_pendiente(EstadoContrato.VIGENTE, 90, set(), False) is None
    assert nivel_alerta_pendiente(EstadoContrato.RENOVADO, 3, set(), False) is None


# ---- validaciones de entidades ----
def _contrato(**k):
    base = dict(id=None, numero="001/2026", objeto="Obra", id_tipo=1, id_contratista=1, id_responsable=1,
                monto=Decimal("10"), fecha_inicio=date(2026, 1, 1), fecha_vencimiento=date(2026, 12, 31))
    base.update(k)
    return Contrato(**base)


def test_contrato_valido():
    assert _contrato().estado == EstadoContrato.REGISTRADO


def test_vencimiento_anterior_al_inicio_se_rechaza():
    with pytest.raises(ErrorValidacion):
        _contrato(fecha_vencimiento=date(2025, 12, 31))


def test_monto_negativo_se_rechaza():
    with pytest.raises(ErrorValidacion):
        _contrato(monto=Decimal("-1"))


@pytest.mark.parametrize("campo", ["numero", "objeto"])
def test_textos_obligatorios(campo):
    with pytest.raises(ErrorValidacion):
        _contrato(**{campo: "   "})


def test_garantia_solo_boleta_o_poliza():
    Garantia(None, 1, "boleta", HOY)
    with pytest.raises(ErrorValidacion):
        Garantia(None, 1, "cheque", HOY)


def test_contratista_y_seguimiento_exigen_datos():
    with pytest.raises(ErrorValidacion):
        Contratista(None, "  ")
    with pytest.raises(ErrorValidacion):
        Seguimiento(None, 1, 1, "   ", None)


# ---- permisos por rol ----
def _u(rol, id_=1):
    return Usuario(id_, "N", "n@x.test", rol, True)


def test_matriz_de_permisos():
    c = _contrato(id=5, id_responsable=1)
    assert permisos.puede_ver_contrato(_u(Rol.RESPONSABLE, 1), c)
    assert not permisos.puede_ver_contrato(_u(Rol.RESPONSABLE, 2), c)
    for rol in (Rol.FUNCIONARIO, Rol.AUTORIDAD, Rol.ADMINISTRADOR):
        assert permisos.puede_ver_contrato(_u(rol, 99), c)
    assert permisos.puede_editar_contratos(_u(Rol.FUNCIONARIO)) and permisos.puede_editar_contratos(_u(Rol.ADMINISTRADOR))
    assert not permisos.puede_editar_contratos(_u(Rol.RESPONSABLE)) and not permisos.puede_editar_contratos(_u(Rol.AUTORIDAD))
    assert permisos.puede_ver_reportes(_u(Rol.AUTORIDAD)) and not permisos.puede_ver_reportes(_u(Rol.RESPONSABLE))
    assert permisos.es_administrador(_u(Rol.ADMINISTRADOR)) and not permisos.es_administrador(_u(Rol.FUNCIONARIO))
    assert not permisos.puede_registrar_seguimiento(_u(Rol.AUTORIDAD), c)


def test_exigir_lanza_permiso_denegado():
    with pytest.raises(PermisoDenegado):
        permisos.exigir(False)
    permisos.exigir(True)
