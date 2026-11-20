# Plan y resultados de pruebas

**Suite automática: 159 pruebas en 4 archivos + 1 módulo de Selenium que se omite sin Chrome.**
Última ejecución completa en el entorno de desarrollo: `159 passed, 1 skipped`.

| Archivo | Pruebas | Qué verifica | ¿Necesita base de datos? |
|---|---|---|---|
| `test_dominio.py` | 29 | Reglas de vencimiento (valores límite 31/30/8/7/0/−1), umbrales, alertas idempotentes, validaciones y permisos | No |
| `test_aplicacion.py` | 62 | Casos de uso con repositorios en memoria, reloj falso y correo simulado: contratos, motor, seguimiento, usuarios, documentos, chatbot | No |
| `test_adaptadores.py` | 12 | Gemini (red simulada), almacén de archivos, lector de PDF/DOCX/TXT | No |
| `test_integracion.py` | 56 | Vistas + PostgreSQL real: acceso, roles, seguridad, documentos, chatbot por HTTP, comandos, datos de demostración | Sí |
| `caja_negra/test_selenium.py` | 2 | Navegador real: login, registro de contrato, chatbot | Sí + Chrome (**no ejecutada en el entorno de desarrollo**) |

## Casos de prueba del informe (CP-01 a CP-14)
| Caso | Pruebas que lo cubren |
|---|---|
| CP-01 Inicio de sesión válido | `test_cp01_login_valido_redirige_al_panel` |
| CP-02 Inicio de sesión inválido | `test_cp02_login_invalido_muestra_mensaje_claro`, `test_login_valido_e_invalido_quedan_en_la_bitacora` |
| CP-03 Registro de contrato | `test_cp03_registrar_contrato_calcula_el_estado` |
| CP-04 Fechas incoherentes | `test_vencimiento_anterior_al_inicio_se_rechaza`, `test_cp04_*` (aplicación e integración) |
| CP-05 Número repetido | `test_cp05_*` (aplicación e integración), `test_la_base_de_datos_misma_protege_la_integridad` |
| CP-06 Contrato a 30 días | `test_cp06_contrato_a_30_dias_genera_aviso` |
| CP-07 Contrato a 7 días | `test_cp07_y_cp13_contrato_a_7_dias_es_critico_con_reloj_falso` |
| CP-08 Contrato vencido | `test_cp08_contrato_vencido_ayer` |
| CP-09 Consulta al chatbot | `test_cp09_que_vence_esta_semana`, `test_cp09_el_chatbot_responde_con_datos_reales` |
| CP-10 Consulta ambigua | `test_cp10_consulta_ambigua_pide_el_numero` |
| CP-11 Acceso sin permiso | `test_cp11_*` (aplicación e integración), `test_acceso_por_rol` |
| CP-12 Bitácora | `test_cp12_*` (aplicación e integración) |
| CP-13 Reglas con adaptadores simulados | `test_cp07_y_cp13_contrato_a_7_dias_es_critico_con_reloj_falso` |
| CP-14 Cambio del adaptador de correo | `test_cp14_cambiar_el_adaptador_de_correo_no_cambia_las_alertas` |

## Seguridad probada (ISO/IEC 27002, guía)
| Amenaza | Prueba |
|---|---|
| Inyección SQL en la búsqueda | `test_inyeccion_sql_en_la_busqueda_no_devuelve_ni_rompe_nada` |
| XSS almacenado | `test_xss_el_contenido_del_usuario_se_escapa` |
| CSRF | `test_csrf_se_exige_en_los_formularios`, `test_csrf_se_exige_tambien_en_el_chatbot` |
| Contraseñas en texto plano | `test_las_contrasenas_se_guardan_con_hash` |
| Sesión y cabeceras | `test_cabeceras_y_cookies_de_sesion_seguras` |
| Acceso por rol y contratos ajenos | `test_acceso_por_rol`, `test_cp11_*`, `test_un_usuario_no_puede_cambiar_roles_si_no_es_admin` |
| Archivos peligrosos o disfrazados | `test_archivos_peligrosos_o_falsos_se_rechazan`, `test_docx_falso_*`, `test_nombre_con_ruta_se_sanea_*` |
| Escape de directorio en el almacén | `test_almacen_rechaza_nombres_que_no_genero_el_sistema` |
| Documentos de contratos ajenos | `test_el_documento_hereda_el_permiso_del_contrato`, `test_documento_de_contrato_ajeno_*`, `test_el_chatbot_no_filtra_documentos_de_contratos_ajenos` |
| Inyección de fórmulas en CSV | `test_el_csv_neutraliza_formulas` |
| Integridad ante fallos | `test_la_transaccion_deshace_todo_si_algo_falla`, restricciones CHECK/UNIQUE |
| Redirección a sitios externos | `test_no_se_sigue_una_redireccion_a_otro_sitio` |

## Cobertura (caja blanca, medida con coverage.py: sentencias y ramas)
Comando: `python -m coverage run --branch --source=contratos_viacha.dominio,contratos_viacha.aplicacion -m pytest` y luego `python -m coverage report`.
Dominio: 100 % (entidades, permisos y reglas de vencimiento). Casos de uso: entre 85 % y 99 %. Total medido: 94 %.
Una cobertura alta no prueba que no haya errores; indica qué líneas y ramas ejecutan las pruebas.

## Rendimiento (medición del desarrollo, NO de su computadora)
Con `medir_tiempos.py` y 500 contratos en PostgreSQL, en el entorno de desarrollo: panel ≈ 40 ms, lista de contratos ≈ 104 ms
(p95 140 ms), filtro por estado ≈ 38 ms, reporte ≈ 22 ms, chatbot con plantillas ≈ 9 ms. Meta propuesta: ≤ 2 s.
Es una medición **de un solo usuario** en otro equipo; la carga con 20 usuarios simultáneos se mide con `locustfile.py`.
**Vuelva a medir en su equipo** antes de citar cifras en la defensa.

## Defectos que las pruebas y la revisión visual encontraron y se corrigieron
1. La búsqueda en documentos no encontraba plurales («multas» frente a «multa»). Con prueba automática.
2. Al subir un archivo vacío a un contrato ajeno se validaba el archivo antes que el permiso. Con prueba automática.
3. La fecha del historial del chatbot salía en hora UTC (un día adelantada). Corregido con `fecha_local` en el puerto del reloj.
4. El botón «Salir» era invisible sobre el encabezado oscuro (hallado al revisar capturas).

## Lo que NO se ha medido
- Precisión del chatbot (exactitud / F1) con preguntas reales: requiere un conjunto de frases de prueba de los funcionarios.
- Carga concurrente con Locust y pruebas con Selenium: los archivos están listos, pero no se ejecutaron en el entorno de desarrollo.
- Análisis de vulnerabilidades con OWASP ZAP.
- Llamadas reales a la API de Gemini (la lógica del adaptador se probó con la red simulada).
- Aceptación por parte de usuarios reales del GAM Viacha.
