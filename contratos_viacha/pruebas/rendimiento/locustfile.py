"""Prueba de CARGA con Locust (20 usuarios concurrentes, meta de la prueba).

1. pip install locust
2. python manage.py cargar_datos_demo   (y arranque el sistema: python manage.py runserver)
3. locust -f contratos_viacha/pruebas/rendimiento/locustfile.py --host http://127.0.0.1:8000 --users 20 --spawn-rate 5 --run-time 1m --headless
Meta propuesta: tiempo de respuesta promedio <= 2 s."""
import json
import re

from locust import HttpUser, between, task


class Funcionario(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        r = self.client.get("/acceso/")
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text).group(1)
        self.client.post("/acceso/", {"correo": "funcionario@viacha.test", "password": "Demo2026!", "csrfmiddlewaretoken": token})

    @task(4)
    def panel(self):
        self.client.get("/", name="panel")

    @task(4)
    def lista(self):
        self.client.get("/contratos/", name="lista de contratos")

    @task(2)
    def alertas(self):
        self.client.get("/alertas/", name="alertas")

    @task(2)
    def chatbot(self):
        token = self.client.cookies.get("csrftoken", "")
        self.client.post("/chatbot/consultar/", data=json.dumps({"mensaje": "¿Qué vence esta semana?"}),
                         headers={"Content-Type": "application/json", "X-CSRFToken": token}, name="chatbot")
