"""Adaptador de entrada: tarea programada. Ejecutar una vez al día (cron o Programador de tareas de Windows):
    python manage.py ejecutar_revision_diaria
"""
from django.core.management.base import BaseCommand

from contratos_viacha import composicion


class Command(BaseCommand):
    help = "Recalcula los estados de los contratos y genera las alertas del día."

    def handle(self, *args, **opciones):
        r = composicion.servicios().revision.ejecutar()
        self.stdout.write(self.style.SUCCESS(
            f"Revisión terminada: {r.contratos_revisados} contratos, {r.estados_actualizados} estados actualizados, "
            f"{r.alertas_generadas} alertas ({r.correos_enviados} enviadas por correo)."))
        for linea in r.detalle:
            self.stdout.write(f"  - {linea}")
