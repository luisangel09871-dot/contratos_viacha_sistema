"""Crea el primer usuario administrador:
    python manage.py crear_administrador --correo admin@gamviacha.gob.bo --nombre "Nombre Apellido"
"""
import getpass

from django.core.management.base import BaseCommand, CommandError

from contratos_viacha import composicion
from contratos_viacha.dominio.entidades import Rol, Usuario
from contratos_viacha.dominio.excepciones import ErrorDeDominio
from contratos_viacha.adaptadores.salida.persistencia.repositorios import RepositorioUsuariosORM


class Command(BaseCommand):
    help = "Crea un usuario con rol administrador."

    def add_arguments(self, parser):
        parser.add_argument("--correo", required=True)
        parser.add_argument("--nombre", required=True)
        parser.add_argument("--password", help="Si se omite, se pide por teclado.")

    def handle(self, *args, **o):
        password = o["password"] or getpass.getpass("Contraseña (mínimo 8 caracteres): ")
        if len(password) < 8:
            raise CommandError("La contraseña debe tener al menos 8 caracteres.")
        repo = RepositorioUsuariosORM()
        if repo.por_correo(o["correo"]):
            raise CommandError("Ya existe un usuario con ese correo.")
        try:
            repo.crear(Usuario(None, o["nombre"].strip(), o["correo"].strip().lower(), Rol.ADMINISTRADOR, True), password)
        except ErrorDeDominio as e:
            raise CommandError(str(e))
        self.stdout.write(self.style.SUCCESS(f"Administrador {o['correo']} creado."))
