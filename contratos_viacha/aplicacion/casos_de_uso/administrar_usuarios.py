"""Casos de uso: inicio de sesión, usuarios y roles, umbrales y bitácora."""
from __future__ import annotations

import re

from ...dominio import permisos
from ...dominio.entidades import Rol, Umbrales, Usuario
from ...dominio.excepciones import CredencialesInvalidas, ErrorValidacion, NoEncontrado
from ..puertos.entrada import AdministrarUsuarios
from ..puertos.salida import RegistroAuditoria, RepositorioUmbrales, RepositorioUsuarios, Transaccion

_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AdministrarUsuariosCU(AdministrarUsuarios):
    def __init__(self, usuarios: RepositorioUsuarios, umbrales: RepositorioUmbrales,
                 auditoria: RegistroAuditoria, transaccion: Transaccion):
        self.usuarios, self.umbrales, self.auditoria, self.transaccion = usuarios, umbrales, auditoria, transaccion

    def iniciar_sesion(self, correo: str, password: str) -> Usuario:
        correo = (correo or "").strip().lower()
        usuario = self.usuarios.verificar_credenciales(correo, password or "")
        if usuario is None or not usuario.activo:
            self.auditoria.registrar(None, "usuario", "LOGIN_FALLIDO", f"Intento de acceso con {correo[:80]}")
            raise CredencialesInvalidas("Usuario o contraseña incorrectos.")
        self.auditoria.registrar(usuario.id, "usuario", "LOGIN", "Inicio de sesión")
        return usuario

    def listar_usuarios(self, actor: Usuario) -> list[Usuario]:
        permisos.exigir(permisos.es_administrador(actor), "Solo el administrador gestiona usuarios.")
        return self.usuarios.listar()

    def crear_usuario(self, actor: Usuario, nombre: str, correo: str, rol: str, password: str) -> Usuario:
        permisos.exigir(permisos.es_administrador(actor), "Solo el administrador gestiona usuarios.")
        nombre, correo = (nombre or "").strip(), (correo or "").strip().lower()
        if not nombre:
            raise ErrorValidacion("El nombre es obligatorio.")
        if not _CORREO.match(correo):
            raise ErrorValidacion("El correo no es válido.")
        try:
            rol_e = Rol(rol)
        except ValueError:
            raise ErrorValidacion("El rol no es válido.")
        if len(password or "") < 8:
            raise ErrorValidacion("La contraseña debe tener al menos 8 caracteres.")
        if self.usuarios.por_correo(correo):
            raise ErrorValidacion("Ya existe un usuario con ese correo.")
        with self.transaccion.atomico():
            nuevo = self.usuarios.crear(Usuario(None, nombre, correo, rol_e, True), password)
            self.auditoria.registrar(actor.id, "usuario", "INSERT", f"Usuario {correo} con rol {rol_e.value}")
        return nuevo

    def _obtener_otro(self, actor: Usuario, id_usuario: int) -> Usuario:
        permisos.exigir(permisos.es_administrador(actor), "Solo el administrador gestiona usuarios.")
        if id_usuario == actor.id:
            raise ErrorValidacion("No puede modificar su propio rol o estado.")
        u = self.usuarios.obtener(id_usuario)
        if u is None:
            raise NoEncontrado("El usuario no existe.")
        return u

    def cambiar_rol(self, actor: Usuario, id_usuario: int, rol: str) -> Usuario:
        u = self._obtener_otro(actor, id_usuario)
        try:
            nuevo_rol = Rol(rol)
        except ValueError:
            raise ErrorValidacion("El rol no es válido.")
        anterior, u.rol = u.rol, nuevo_rol
        with self.transaccion.atomico():
            guardado = self.usuarios.actualizar(u)
            self.auditoria.registrar(actor.id, "usuario", "UPDATE", f"{u.correo}: rol {anterior.value} -> {nuevo_rol.value}")
        return guardado

    def activar(self, actor: Usuario, id_usuario: int, activo: bool) -> Usuario:
        u = self._obtener_otro(actor, id_usuario)
        u.activo = activo
        with self.transaccion.atomico():
            guardado = self.usuarios.actualizar(u)
            self.auditoria.registrar(actor.id, "usuario", "UPDATE", f"{u.correo}: {'activado' if activo else 'desactivado'}")
        return guardado

    def obtener_umbrales(self, actor: Usuario) -> Umbrales:
        return self.umbrales.obtener()

    def configurar_umbrales(self, actor: Usuario, umbrales: Umbrales) -> Umbrales:
        permisos.exigir(permisos.es_administrador(actor), "Solo el administrador configura los umbrales.")
        with self.transaccion.atomico():
            self.umbrales.guardar(umbrales)
            self.auditoria.registrar(actor.id, "umbral_alerta", "UPDATE",
                                     f"Umbrales: próximo={umbrales.dias_proximo}, crítico={umbrales.dias_critico}, "
                                     f"avisos={umbrales.aviso_1}/{umbrales.aviso_2}")
        return umbrales

    def bitacora(self, actor: Usuario, limite: int = 200) -> list:
        permisos.exigir(permisos.es_administrador(actor), "Solo el administrador consulta la bitácora.")
        return self.auditoria.listar(limite)
