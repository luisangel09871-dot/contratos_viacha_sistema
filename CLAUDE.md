# CLAUDE.md - Guía de Proyecto para Claude Code

## Descripción General
Sistema web con chatbot para la gestión de contratos y control de vencimientos del **Gobierno Autónomo Municipal de Viacha**.
Desarrollado en **Python + Django + PostgreSQL** siguiendo los principios de **Arquitectura Hexagonal (Puertos y Adaptadores)**.

---

## Arquitectura y Estructura del Código
El código se organiza en `contratos_viacha/` separando responsabilidades:
- **`dominio/`**: Reglas de negocio puras, modelos de dominio y entidades independientes del framework.
- **`aplicacion/`**: Casos de uso (`casos_de_uso/`), puertos de entrada y orquestación de la lógica.
- **`infraestructura/`**: Adaptadores secundarios (repositorios de base de datos Django ORM, servicios externos, integraciones de correo y LLM/Gemini).
- **`presentacion/` o interfaces**: Vistas Django, formularios, URLs y controladores web.

> **Regla de oro de arquitectura:** El dominio no debe depender de Django ni de la base de datos. Las dependencias siempre apuntan hacia adentro.

---

## Comandos Frecuentes

### Entorno y Ejecución
- **Activar entorno virtual:** `.venv\Scripts\Activate.ps1` (Windows) o `source .venv/bin/activate` (Linux/Mac)
- **Instalar dependencias:** `pip install -r requirements.txt`
- **Servidor de desarrollo:** `python manage.py runserver`
- **Migraciones:** 
  - `python manage.py makemigrations`
  - `python manage.py migrate`
- **Carga de datos demo:** `python manage.py cargar_datos_demo`

### Pruebas y Calidad
- **Ejecutar tests:** `pytest`
- **Ejecutar tests específicos:** `pytest tests/ruta_al_test.py`

---

## Estándares y Buenas Prácticas
1. **Tipado estricto:** Usar type hints de Python (`typing`) en funciones y métodos.
2. **Casos de uso desacoplados:** Cada caso de uso debe representar una acción concreta del sistema.
3. **Manejo de excepciones:** Emplear excepciones de dominio específicas antes de propagar errores genéricos.
4. **Persistencia:** Cualquier acceso a datos mediante Django ORM debe implementarse a través de adaptadores de infraestructura que implementen los puertos definidos.
