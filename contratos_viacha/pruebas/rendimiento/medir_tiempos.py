"""Medición rápida de tiempos de respuesta SIN instalar nada extra (usa el cliente de pruebas de Django).
Crea una base de pruebas con 500 contratos, mide cada pantalla y muestra promedio, máximo y percentil 95.

    python manage.py shell -c "from contratos_viacha.pruebas.rendimiento.medir_tiempos import ejecutar; ejecutar()"
Atención: usa la base configurada en DATABASE_URL y deja datos de prueba; úsela sobre una base de pruebas."""
import json
import statistics
import time
from datetime import date, timedelta
from decimal import Decimal


def ejecutar(n_contratos: int = 500, repeticiones: int = 30):
    from django.test import Client
    from contratos_viacha import composicion
    from contratos_viacha.adaptadores.salida.persistencia import models as m
    from contratos_viacha.adaptadores.salida.persistencia.repositorios import RepositorioUsuariosORM
    from contratos_viacha.dominio.entidades import Rol, Usuario

    s = composicion.servicios()
    repo = RepositorioUsuariosORM()
    func = repo.por_correo("medicion@viacha.test") or repo.crear(Usuario(None, "Medición", "medicion@viacha.test", Rol.FUNCIONARIO, True), "Medicion2026!")
    contratista = m.ContratistaModelo.objects.first() or m.ContratistaModelo.objects.create(razon_social="Medición S.R.L.")
    existentes = m.ContratoModelo.objects.count()
    if existentes < n_contratos:
        hoy = s.consultar.reloj.hoy()
        m.ContratoModelo.objects.bulk_create([
            m.ContratoModelo(numero=f"M{i:05d}/{hoy.year}", objeto=f"Contrato de medición {i}", tipo_id=1 + i % 4, contratista_id=contratista.id,
                             responsable_id=func.id, monto=Decimal(1000 + i), fecha_inicio=hoy - timedelta(days=100),
                             fecha_vencimiento=hoy + timedelta(days=(i * 7) % 400 - 40), estado="vigente")
            for i in range(n_contratos - existentes)])
    c = Client()
    c.post("/acceso/", {"correo": "medicion@viacha.test", "password": "Medicion2026!"})
    pruebas = {"panel": lambda: c.get("/"), "lista de contratos": lambda: c.get("/contratos/"),
               "filtro por estado": lambda: c.get("/contratos/?estado=critico"),
               "reporte por vencer": lambda: c.get("/reportes/?tipo=por_vencer"),
               "chatbot (plantillas)": lambda: c.post("/chatbot/consultar/", data=json.dumps({"mensaje": "¿Qué vence esta semana?"}), content_type="application/json")}
    print(f"\nContratos en la base: {m.ContratoModelo.objects.count()} | repeticiones por pantalla: {repeticiones}\n")
    print(f"{'Pantalla':26s}{'promedio':>10s}{'p95':>10s}{'máximo':>10s}")
    for nombre, f in pruebas.items():
        f()  # calentamiento
        t = []
        for _ in range(repeticiones):
            ini = time.perf_counter(); r = f(); t.append(time.perf_counter() - ini); assert r.status_code == 200
        t.sort()
        print(f"{nombre:26s}{statistics.mean(t) * 1000:8.0f}ms{t[int(len(t) * .95) - 1] * 1000:8.0f}ms{max(t) * 1000:8.0f}ms")
