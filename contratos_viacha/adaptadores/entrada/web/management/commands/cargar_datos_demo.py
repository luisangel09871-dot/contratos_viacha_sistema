"""Carga datos FICTICIOS de demostración (usuarios, contratistas, ~25 contratos en todos los estados,
garantías, seguimientos y dos documentos) usando los mismos casos de uso que la aplicación.

    python manage.py cargar_datos_demo            # carga si no hay datos de demostración
    python manage.py cargar_datos_demo --reiniciar # borra TODO y vuelve a cargar
Todos los datos son de ejemplo; los contratos llevan el prefijo [EJEMPLO]."""
import io
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from contratos_viacha import composicion
from contratos_viacha.adaptadores.salida.correo import NotificadorSimulado
from contratos_viacha.adaptadores.salida.persistencia import models as m
from contratos_viacha.adaptadores.salida.persistencia.repositorios import RepositorioUsuariosORM
from contratos_viacha.dominio.entidades import Rol, Usuario

CLAVE_DEMO = "Demo2026!"
USUARIOS = [
    ("Admin de Ejemplo", "admin@viacha.test", Rol.ADMINISTRADOR),
    ("Funcionaria de Contrataciones (ejemplo)", "funcionario@viacha.test", Rol.FUNCIONARIO),
    ("Responsable Uno (ejemplo)", "responsable1@viacha.test", Rol.RESPONSABLE),
    ("Responsable Dos (ejemplo)", "responsable2@viacha.test", Rol.RESPONSABLE),
    ("Autoridad Jurídica (ejemplo)", "autoridad@viacha.test", Rol.AUTORIDAD),
]
CONTRATISTAS = ["Constructora Altiplano S.R.L.", "Servicios Andinos Ltda.", "Ingeniería y Obras Ingavi S.A.",
                "Provisiones del Sur S.R.L.", "Consultora Illimani", "Mantenimiento Técnico El Alto S.R.L.",
                "Suministros Viacha Ltda.", "Constructora Tiwanaku S.A.", "Consultores Asociados Titicaca",
                "Transportes y Equipos Aroma S.R.L."]
OBJETOS = ["Construcción de cancha polifuncional", "Provisión de material de escritorio", "Mantenimiento de alumbrado público",
           "Consultoría para estudio de factibilidad de agua potable", "Refacción de la unidad educativa", "Adquisición de luminarias LED",
           "Servicio de limpieza de oficinas municipales", "Construcción de empedrado en calle principal", "Provisión de mobiliario para el centro de salud",
           "Supervisión técnica de obra vial", "Servicio de internet institucional", "Mejoramiento de plaza principal",
           "Consultoría de diseño de sistema de riego", "Provisión de uniformes para personal operativo", "Mantenimiento de vehículos municipales",
           "Construcción de muro de contención", "Servicio de vigilancia", "Adquisición de equipos de cómputo", "Ampliación de red de alcantarillado",
           "Consultoría de auditoría de procesos", "Provisión de combustible", "Construcción de sede social", "Servicio de fotocopiado",
           "Refacción del mercado central", "Provisión de materiales de construcción"]
# días desde hoy hasta el vencimiento: 3 vencidos, 4 críticos, 5 próximos, 9 vigentes y 4 que se cierran a mano
DIAS = [-45, -20, -3, 0, 2, 5, 7, 9, 14, 20, 26, 30, 45, 60, 90, 120, 150, 180, 240, 300, 365, 75, 100, 200, 130]
FINALES = {21: "renovado", 22: "renovado", 23: "terminado", 24: "terminado"}  # posiciones en DIAS
MONTOS = [85000, 12400, 230000, 48000, 960000, 31500, 77000, 450000, 18000, 125000]

TEXTO_CLAUSULAS = """CONTRATO ADMINISTRATIVO DE EJEMPLO - CLAUSULAS (DOCUMENTO FICTICIO)

CLAUSULA QUINTA (PLAZO). El plazo de ejecucion es de 180 dias calendario computables desde la fecha de la orden de proceder.

CLAUSULA SEPTIMA (MULTAS). Por cada dia de retraso en la entrega se aplicara una multa del 0,3 por ciento del monto total del contrato, hasta un maximo del 10 por ciento.

CLAUSULA OCTAVA (GARANTIA). El contratista presentara una boleta de garantia de cumplimiento de contrato equivalente al 7 por ciento del monto, con vigencia hasta 30 dias despues del plazo contractual.

CLAUSULA DECIMA (RESOLUCION). La entidad podra resolver el contrato por incumplimiento reiterado de las obligaciones, previa notificacion escrita."""


class Command(BaseCommand):
    help = "Carga datos ficticios de demostración."

    def add_arguments(self, parser):
        parser.add_argument("--reiniciar", action="store_true", help="Borra todos los datos antes de cargar.")

    def handle(self, *args, **o):
        if o["reiniciar"]:
            for mod in (m.ConsultaChatbotModelo, m.AuditoriaModelo, m.DocumentoModelo, m.AlertaModelo, m.SeguimientoModelo,
                        m.GarantiaModelo, m.ContratoModelo, m.ContratistaModelo):
                mod.objects.all().delete()
            m.UsuarioModelo.objects.filter(correo__endswith="@viacha.test").delete()
        if m.ContratoModelo.objects.filter(numero__startswith="001/").exists():
            raise CommandError("Ya hay datos de demostración. Use --reiniciar para borrarlos y cargarlos de nuevo.")

        s = composicion.construir(notificador=NotificadorSimulado(funciona=False), modelo=None)
        repo_u = RepositorioUsuariosORM()
        ids = {}
        for nombre, correo, rol in USUARIOS:
            u = repo_u.por_correo(correo) or repo_u.crear(Usuario(None, nombre, correo, rol, True), CLAVE_DEMO)
            ids[correo] = u
        admin, func = ids["admin@viacha.test"], ids["funcionario@viacha.test"]
        resp = [ids["responsable1@viacha.test"], ids["responsable2@viacha.test"]]

        contratistas = [s.gestionar.registrar_contratista(func, {"razon_social": n + " (ejemplo)", "nit": f"100000{i:04d}",
                                                                  "correo_contacto": f"contacto{i}@ejemplo.test"})
                        for i, n in enumerate(CONTRATISTAS, 1)]
        tipos = [i for i, _ in s.gestionar.catalogos(func)["tipos"]]
        hoy = s.consultar.reloj.hoy()

        contratos = []
        for i, dias in enumerate(DIAS):
            venc = hoy + timedelta(days=dias)
            ini = venc - timedelta(days=365 if i % 2 else 180)
            datos = dict(numero=f"{i + 1:03d}/{hoy.year}", objeto=f"[EJEMPLO] {OBJETOS[i]}", id_tipo=tipos[i % len(tipos)],
                         id_contratista=contratistas[i % len(contratistas)].id, id_responsable=resp[i % 2].id,
                         monto=Decimal(MONTOS[i % len(MONTOS)] + i * 1000), fecha_inicio=ini, fecha_vencimiento=venc)
            if i % 2 == 0:  # garantía en la mitad de los contratos
                datos.update(garantia_tipo="boleta" if i % 4 == 0 else "poliza",
                             garantia_vencimiento=venc + timedelta(days=(0 if i % 3 else 10)))
            contratos.append(s.gestionar.registrar_contrato(func, datos))
        for pos, estado in FINALES.items():
            s.gestionar.marcar_estado_final(func, contratos[pos].id, estado)

        acciones = ["Se solicitó al contratista la ampliación de la garantía.", "Se consultó a jurídica sobre la renovación.",
                    "Se notificó por nota al contratista el vencimiento próximo.", "Se coordinó reunión de cierre con la unidad solicitante."]
        for i in (0, 1, 3, 4, 8):
            s.seguimiento.registrar(resp[i % 2] if i % 2 == 0 else resp[1], contratos[i].id, acciones[i % len(acciones)])

        # dos documentos de ejemplo, subidos con el mismo caso de uso que la aplicación
        s.subir_documento.subir(func, contratos[3].id, "clausulas_ejemplo.txt", TEXTO_CLAUSULAS.encode("utf-8"))
        from docx import Document
        d = Document()
        d.add_heading("Acta de recepción provisional (documento ficticio)", level=1)
        d.add_paragraph("Se realizó la recepción provisional de la obra con observaciones menores. El contratista tiene 15 días calendario para subsanarlas.")
        d.add_paragraph("La boleta de garantía de cumplimiento permanecerá vigente hasta la recepción definitiva.")
        buf = io.BytesIO()
        d.save(buf)
        s.subir_documento.subir(func, contratos[4].id, "acta_recepcion_ejemplo.docx", buf.getvalue())

        r = s.revision.ejecutar()
        self.stdout.write(self.style.SUCCESS(
            f"Datos de demostración cargados: {len(contratos)} contratos, {len(contratistas)} contratistas, {r.alertas_generadas} alertas."))
        self.stdout.write(f"Usuarios de ejemplo (contraseña de todos: {CLAVE_DEMO}):")
        for nombre, correo, rol in USUARIOS:
            self.stdout.write(f"  {correo:30s} {rol.etiqueta}")
