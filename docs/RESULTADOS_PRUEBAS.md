# Resultados de la ejecución de pruebas

Ejecución del 20 de noviembre de 2026 con PostgreSQL 16 local y Python 3.13: **159 aprobadas, 1 omitida** (Selenium, requiere Chrome).

```
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-9.1.1, pluggy-1.6.0
django: version: 5.2.19, settings: contratos_viacha.configuracion.settings (from ini)
rootdir: /home/claude/luisangel09871-dot/contratos_viacha_sistema
configfile: pytest.ini
testpaths: contratos_viacha/pruebas
plugins: platformdirs-4.13.5, anyio-4.15.1, django-4.14.0
collected 159 items / 1 skipped
contratos_viacha/pruebas/test_integracion.py ........................... [ 16%]
.............................                                            [ 35%]
contratos_viacha/pruebas/test_adaptadores.py ............                [ 42%]
contratos_viacha/pruebas/test_aplicacion.py ............................ [ 60%]
..................................                                       [ 81%]
contratos_viacha/pruebas/test_dominio.py .............................   [100%]
======================== 159 passed, 1 skipped in 3.31s ========================
```
