# Sistema web con chatbot para la gestión de contratos y control de vencimientos
**Gobierno Autónomo Municipal de Viacha** · Proyecto Integrador Intermedio II · Luis Angel Yauli Huanca

Sistema en **Python + Django + PostgreSQL** con **arquitectura hexagonal** (puertos y adaptadores). Registra contratos, calcula
sus estados con reglas determinísticas, genera alertas antes de los vencimientos y ofrece un **chatbot** que responde sobre
contratos y sobre el contenido de los **documentos** que se suben a cada contrato.

> Todos los datos de `cargar_datos_demo` y de `base_datos/datos_demo.sql` son **ficticios**.

## 1. Requisitos
- Python 3.11 o superior (marque «Add Python to PATH» al instalar).
- PostgreSQL 14 o superior con pgAdmin 4.
- Opcional: clave de Gemini (Google AI Studio) y una cuenta SMTP.

## 2. Instalación (Windows, PowerShell)
```powershell
# 1) Cree una base VACÍA llamada contratos_viacha (pgAdmin: clic derecho en Databases > Create > Database)

# 2) Entorno virtual y dependencias
cd contratos_viacha_sistema
python -m venv .venv
.venv\Scripts\Activate.ps1          # si PowerShell lo bloquea: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt

# 3) Configuración
copy .env.example .env
notepad .env                         # ponga SU contraseña de PostgreSQL en DATABASE_URL

# 4) Tablas y datos
python manage.py migrate
python manage.py cargar_datos_demo   # datos ficticios para la demostración (o: crear_administrador)

# 5) Iniciar
python manage.py runserver           # abra http://127.0.0.1:8000
```
En Linux o macOS es igual, con `source .venv/bin/activate` y `cp .env.example .env`.

**Usuarios de demostración** (contraseña de todos: `Demo2026!`)

| Correo | Rol | Qué puede hacer |
|---|---|---|
| admin@viacha.test | Administrador | Todo, incluidos usuarios, umbrales y bitácora |
| funcionario@viacha.test | Funcionario de contrataciones | Registrar y editar contratos, contratistas y garantías; reportes |
| responsable1@viacha.test | Responsable de contrato | Solo ve sus contratos y alertas; registra seguimiento y sube documentos |
| responsable2@viacha.test | Responsable de contrato | Igual, con otros contratos (sirve para demostrar que no ve los ajenos) |
| autoridad@viacha.test | Autoridad / jurídica | Solo lectura: panel, contratos y reportes |

Para un sistema real, no cargue datos de demostración: cree el administrador con
`python manage.py crear_administrador --correo su@correo --nombre "Su Nombre"` y registre los contratos reales.

## 3. Revisión diaria de vencimientos
El motor recalcula estados y genera alertas con:
```powershell
python manage.py ejecutar_revision_diaria
```
Prográmelo una vez al día (Windows: **Programador de tareas** > acción «Iniciar un programa» con
`C:\ruta\.venv\Scripts\python.exe` y argumentos `manage.py ejecutar_revision_diaria`; Linux: `cron`).
Es **idempotente**: ejecutarlo dos veces el mismo día no duplica alertas, y si un día no corrió, se pone al día.

## 4. Chatbot con Gemini (opcional)
1. Cree una clave en <https://aistudio.google.com> y póngala en `.env` como `GEMINI_API_KEY=...`.
2. Escriba en `GEMINI_MODELO` un modelo gratuito vigente que vea en AI Studio (los nombres cambian con el tiempo).
3. Verifique: `python manage.py probar_gemini`. Revise también su cuota en AI Studio.

Gemini **solo redacta** datos que el sistema ya consultó; nunca calcula fechas ni estados. **Sin clave, o si Gemini falla,
el chatbot responde con plantillas y sigue funcionando.** Cada consulta guarda qué adaptador respondió.
Con el plan gratuito, Google puede usar lo enviado para mejorar sus productos: no envíe contratos reales sin revisar las condiciones.

## 5. Correo
Sin configuración, las alertas por correo se imprimen en la consola del servidor (modo demostración). Para enviarlas de verdad,
complete `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` en `.env`.

## 6. Pruebas
```powershell
python -m pytest                         # dominio, casos de uso, adaptadores e integración (usa PostgreSQL)
$env:SELENIUM=1; python -m pytest contratos_viacha/pruebas/caja_negra -v      # navegador real (requiere Chrome)
pip install coverage                     # cobertura: coverage run --branch --source=contratos_viacha.dominio,contratos_viacha.aplicacion -m pytest
pip install locust                       # prueba de carga: ver contratos_viacha/pruebas/rendimiento/locustfile.py
python manage.py shell -c "from contratos_viacha.pruebas.rendimiento.medir_tiempos import ejecutar; ejecutar()"
```
Las pruebas de integración crean y borran su propia base `test_...`; el usuario de PostgreSQL necesita permiso para crear bases.
Detalle del plan de pruebas en `docs/PRUEBAS.md`.

## 7. Base de datos para pgAdmin 4
`base_datos/esquema.sql` (tablas y datos base) y `base_datos/datos_demo.sql` (datos ficticios) sirven para **ver y documentar**
la base en pgAdmin (clic derecho en la base > **ERD Tool** genera el diagrama entidad-relación). Para **ejecutar el sistema**,
cree las tablas siempre con `python manage.py migrate`: el esquema SQL no incluye las tablas internas de Django (sesiones, etc.).

## 8. Arquitectura (resumen; detalle en `docs/ARQUITECTURA.md`)
```
contratos_viacha/
  dominio/        entidades y reglas en Python puro (sin Django, sin base de datos)
  aplicacion/
    puertos/      entrada.py (lo que el sistema ofrece) y salida.py (lo que necesita)
    casos_de_uso/ lógica de aplicación; solo conoce los puertos
  adaptadores/
    entrada/web/  vistas, formularios, plantillas, comandos (revisión diaria, demo, administrador)
    salida/       PostgreSQL (repositorios), correo, almacén de archivos, lector de PDF/DOCX, Gemini, clasificador
  composicion.py  único lugar donde se conectan casos de uso con adaptadores concretos
  pruebas/        dobles en memoria + pruebas por capa
```
La regla central: **las dependencias apuntan hacia el dominio**. Por eso las reglas de vencimiento se prueban con un reloj
falso y repositorios en memoria, sin base de datos, y cambiar el correo o el modelo de lenguaje es escribir otro adaptador.

## 9. Seguridad implementada
Contraseñas con hash (PBKDF2) · sesión de 30 minutos de inactividad con cookie HttpOnly/SameSite · CSRF en formularios y chatbot ·
permisos por rol aplicados en los casos de uso (no solo en las vistas) · consultas parametrizadas (ORM) · escape de HTML en
plantillas y en el chat (`textContent`) · validación de archivos por extensión, tamaño y contenido real · nombre aleatorio en
disco y ruta verificada · los documentos heredan el permiso de su contrato (también en el chatbot) · bitácora de auditoría con
usuario, operación y fecha · neutralización de fórmulas en CSV · restricciones CHECK y UNIQUE en la base de datos ·
transacciones al registrar contratos con garantía · clave de Gemini solo por variable de entorno.

## 10. Limitaciones conocidas (dígalas con honestidad en la defensa)
- No hay bloqueo de cuenta tras varios intentos fallidos de acceso (la contraseña se verifica siempre con tiempo similar).
- No hay recuperación de contraseña por correo: el administrador puede crear usuarios, pero no restablecer claves desde la interfaz.
- El chatbot reconoce 8 intenciones con reglas de palabras clave; Gemini apoya la clasificación solo si las reglas no reconocen nada.
  La precisión del chatbot **no está medida**: habría que evaluarla con preguntas reales de los funcionarios.
- La búsqueda en documentos es por palabras clave (con plural simple), no semántica. Los PDF escaneados (imágenes) no tienen texto extraíble.
- No incluye certificación ISO ni se declara conforme a ISO/IEC 27001: los controles de 27002 se usan como guía.
- Los umbrales de alerta (30/15/7 días) son una propuesta que debe aprobar el GAM Viacha.
