"""Pruebas de CAJA NEGRA con Selenium (navegador real): inicio de sesión, registro de contrato y chatbot.

Requisitos: Google Chrome instalado y `pip install selenium` (Selenium 4 descarga el driver solo).
Se ejecutan con:   SELENIUM=1 python -m pytest contratos_viacha/pruebas/caja_negra -v
Sin SELENIUM=1 (o sin Chrome) las pruebas se OMITEN: no cuentan como aprobadas ni como fallidas."""
import os

import pytest

if os.environ.get("SELENIUM") != "1":
    pytest.skip("Defina SELENIUM=1 para ejecutar las pruebas con navegador.", allow_module_level=True)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from contratos_viacha.pruebas.conftest import CLAVE


@pytest.fixture
def navegador():
    opciones = webdriver.ChromeOptions()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1280,900")
    try:
        driver = webdriver.Chrome(options=opciones)
    except Exception as e:  # sin Chrome o sin driver
        pytest.skip(f"No se pudo iniciar Chrome: {e}")
    driver.implicitly_wait(3)
    yield driver
    driver.quit()


def esperar(driver, localizador):
    return WebDriverWait(driver, 8).until(EC.presence_of_element_located(localizador))


def entrar(driver, url, correo):
    driver.get(url + "/acceso/")
    driver.find_element(By.NAME, "correo").send_keys(correo)
    driver.find_element(By.NAME, "password").send_keys(CLAVE)
    driver.find_element(By.CSS_SELECTOR, "form button[type=submit]").click()


@pytest.mark.django_db(transaction=True)
def test_login_registro_de_contrato_y_chatbot(live_server, mundo, navegador):
    # 1. inicio de sesión
    entrar(navegador, live_server.url, mundo.func.correo)
    assert "Panel de control" in esperar(navegador, (By.TAG_NAME, "h1")).text
    # 2. registro de un contrato
    navegador.get(live_server.url + "/contratos/nuevo/")
    navegador.find_element(By.NAME, "numero").send_keys("900/2026")
    navegador.find_element(By.NAME, "objeto").send_keys("Contrato registrado desde Selenium")
    navegador.find_element(By.NAME, "monto").send_keys("1500.00")
    navegador.execute_script("document.getElementsByName('fecha_inicio')[0].value='2026-06-01';"
                             "document.getElementsByName('fecha_vencimiento')[0].value='2027-06-01';")
    navegador.find_element(By.CSS_SELECTOR, "form.formulario button[type=submit]").click()
    assert "900/2026" in esperar(navegador, (By.TAG_NAME, "h1")).text
    # 3. consulta al chatbot
    navegador.find_element(By.ID, "chat-abrir").click()
    navegador.find_element(By.ID, "chat-texto").send_keys("¿Cómo está el contrato 900/2026?")
    navegador.find_element(By.ID, "chat-enviar").click()
    WebDriverWait(navegador, 8).until(lambda d: "Contrato 900/2026" in d.find_element(By.ID, "chat-msgs").text)


@pytest.mark.django_db(transaction=True)
def test_login_invalido_muestra_el_error(live_server, mundo, navegador):
    navegador.get(live_server.url + "/acceso/")
    navegador.find_element(By.NAME, "correo").send_keys(mundo.func.correo)
    navegador.find_element(By.NAME, "password").send_keys("incorrecta")
    navegador.find_element(By.CSS_SELECTOR, "form button[type=submit]").click()
    assert "incorrectos" in esperar(navegador, (By.CLASS_NAME, "msg-error")).text
