"""Fixtures de las pruebas de integración (PostgreSQL real + Django). Las pruebas de dominio y de
aplicación no las usan: corren sin base de datos."""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from django.test import Client

from contratos_viacha import composicion
from contratos_viacha.adaptadores.salida.almacen import AlmacenLocal
from contratos_viacha.adaptadores.salida.correo import NotificadorSimulado
from contratos_viacha.adaptadores.salida.persistencia.repositorios import RepositorioUsuariosORM
from contratos_viacha.adaptadores.salida.reloj import RelojFalso
from contratos_viacha.dominio.entidades import Rol, Usuario

HOY = date(2026, 11, 10)
CLAVE = "clave-segura-123"


@pytest.fixture(autouse=True)
def hash_rapido(settings):
    settings.PASSWORD_HASHERS = ["contratos_viacha.pruebas.hashers.RapidoPBKDF2"]


@pytest.fixture
def svc(tmp_path, monkeypatch):
    """Servicios reales (PostgreSQL) con reloj fijo, correo simulado, almacén temporal y sin modelo de lenguaje."""
    s = composicion.construir(reloj=RelojFalso(HOY), notificador=NotificadorSimulado(), almacen=AlmacenLocal(tmp_path / "docs"), modelo=None)
    monkeypatch.setattr(composicion, "servicios", lambda: s)
    s.carpeta_docs = tmp_path / "docs"
    return s


@pytest.fixture
def mundo(svc, db):
    repo = RepositorioUsuariosORM()
    u = lambda nombre, rol: repo.crear(Usuario(None, nombre, f"{nombre.lower().replace(' ', '')}@prueba.test", rol, True), CLAVE)
    m = SimpleNamespace(svc=svc, admin=u("Admin", Rol.ADMINISTRADOR), func=u("Funcionaria", Rol.FUNCIONARIO),
                        resp1=u("Responsable Uno", Rol.RESPONSABLE), resp2=u("Responsable Dos", Rol.RESPONSABLE),
                        autoridad=u("Autoridad", Rol.AUTORIDAD))
    m.contratista = svc.gestionar.registrar_contratista(m.func, {"razon_social": "Constructora Prueba", "nit": "999"})

    def contrato(dias, numero, responsable=None, **extra):
        d = dict(numero=numero, objeto=f"Objeto {numero}", id_tipo=1, id_contratista=m.contratista.id,
                 id_responsable=(responsable or m.resp1).id, monto=1000, fecha_inicio=HOY + timedelta(days=dias - 180),
                 fecha_vencimiento=HOY + timedelta(days=dias))
        d.update(extra)
        return svc.gestionar.registrar_contrato(m.func, d)
    m.contrato = contrato
    return m


@pytest.fixture
def entrar():
    def _entrar(usuario, **kw):
        c = Client(**kw)
        r = c.post("/acceso/", {"correo": usuario.correo, "password": CLAVE})
        assert r.status_code == 302, "no se pudo iniciar sesión en la prueba"
        return c
    return _entrar
