-- ==============================================================
-- DATOS DE DEMOSTRACIÓN (TODOS FICTICIOS). Ejecutar DESPUÉS de esquema.sql.
-- Usuarios de ejemplo: admin@viacha.test, funcionario@viacha.test, responsable1@viacha.test,
-- responsable2@viacha.test y autoridad@viacha.test. Contraseña de todos: Demo2026!
-- Las fechas de los contratos son fijas (se calcularon el día de la generación), por lo que
-- el estado mostrado se recalcula con la fecha de hoy al abrir el sistema.
-- Los documentos subidos no se incluyen (los archivos viven en la carpeta almacen_documentos).
-- ==============================================================
-- PostgreSQL database dump


-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

-- Data for Name: contratista; Type: TABLE DATA; Schema: public; Owner: -

INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (34, 'Constructora Altiplano S.R.L. (ejemplo)', '1000000001', 'contacto1@ejemplo.test');
INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (35, 'Servicios Andinos Ltda. (ejemplo)', '1000000002', 'contacto2@ejemplo.test');
INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (36, 'Ingeniería y Obras Ingavi S.A. (ejemplo)', '1000000003', 'contacto3@ejemplo.test');
INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (37, 'Provisiones del Sur S.R.L. (ejemplo)', '1000000004', 'contacto4@ejemplo.test');
INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (38, 'Consultora Illimani (ejemplo)', '1000000005', 'contacto5@ejemplo.test');
INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (39, 'Mantenimiento Técnico El Alto S.R.L. (ejemplo)', '1000000006', 'contacto6@ejemplo.test');
INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (40, 'Suministros Viacha Ltda. (ejemplo)', '1000000007', 'contacto7@ejemplo.test');
INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (41, 'Constructora Tiwanaku S.A. (ejemplo)', '1000000008', 'contacto8@ejemplo.test');
INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (42, 'Consultores Asociados Titicaca (ejemplo)', '1000000009', 'contacto9@ejemplo.test');
INSERT INTO public.contratista (id_contratista, razon_social, nit, correo_contacto) VALUES (43, 'Transportes y Equipos Aroma S.R.L. (ejemplo)', '1000000010', 'contacto10@ejemplo.test');

-- Data for Name: unidad_organizacional; Type: TABLE DATA; Schema: public; Owner: -

-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: -

INSERT INTO public.usuario (last_login, id_usuario, nombre_completo, correo, password_hash, activo, id_rol, id_unidad) VALUES (NULL, 34, 'Admin de Ejemplo', 'admin@viacha.test', 'pbkdf2_sha256$1000000$1S62pB0xJT2E60aVG8Ko1l$OvbJa52Y6CDTc55WJJkmhssJtMxu+3xDbC+J6nY55IE=', true, 4, NULL);
INSERT INTO public.usuario (last_login, id_usuario, nombre_completo, correo, password_hash, activo, id_rol, id_unidad) VALUES (NULL, 35, 'Funcionaria de Contrataciones (ejemplo)', 'funcionario@viacha.test', 'pbkdf2_sha256$1000000$RZfaC8NvO361V4klZPc4Zc$D27gLXMW70TelWG649dCkPg25C2Nx87BkXfrMnrPt1k=', true, 1, NULL);
INSERT INTO public.usuario (last_login, id_usuario, nombre_completo, correo, password_hash, activo, id_rol, id_unidad) VALUES (NULL, 36, 'Responsable Uno (ejemplo)', 'responsable1@viacha.test', 'pbkdf2_sha256$1000000$mjpj6gx6uCUkNKqwsMcFU9$27QRyV7JJdzkysM+WD5orihs+AxFtK+Q1z0nclFg6Os=', true, 2, NULL);
INSERT INTO public.usuario (last_login, id_usuario, nombre_completo, correo, password_hash, activo, id_rol, id_unidad) VALUES (NULL, 37, 'Responsable Dos (ejemplo)', 'responsable2@viacha.test', 'pbkdf2_sha256$1000000$DFl63uB92juDPfE5g021lW$fnWKx5FU7FWpVX0ZNrsqkdtLa7Xa/4wnuh3kBxXwYnY=', true, 2, NULL);
INSERT INTO public.usuario (last_login, id_usuario, nombre_completo, correo, password_hash, activo, id_rol, id_unidad) VALUES (NULL, 38, 'Autoridad Jurídica (ejemplo)', 'autoridad@viacha.test', 'pbkdf2_sha256$1000000$2YWzmVljqfIp48x6Pbe04h$sx+tJHpUqIfOFlDTqJ/qKM0kvKdRRH1oB4tSzwJ5mrw=', true, 3, NULL);

-- Data for Name: contrato; Type: TABLE DATA; Schema: public; Owner: -

INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (34, '001/2026', '[EJEMPLO] Construcción de cancha polifuncional', 85000.00, '2026-03-31', '2026-09-27', 'vencido', 34, 36, 1);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (35, '002/2026', '[EJEMPLO] Provisión de material de escritorio', 13400.00, '2025-10-22', '2026-10-22', 'vencido', 35, 37, 2);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (36, '003/2026', '[EJEMPLO] Mantenimiento de alumbrado público', 232000.00, '2026-05-12', '2026-11-08', 'vencido', 36, 36, 3);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (37, '004/2026', '[EJEMPLO] Consultoría para estudio de factibilidad de agua potable', 51000.00, '2025-11-11', '2026-11-11', 'critico', 37, 37, 4);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (38, '005/2026', '[EJEMPLO] Refacción de la unidad educativa', 964000.00, '2026-05-17', '2026-11-13', 'critico', 38, 36, 1);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (39, '006/2026', '[EJEMPLO] Adquisición de luminarias LED', 36500.00, '2025-11-16', '2026-11-16', 'critico', 39, 37, 2);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (40, '007/2026', '[EJEMPLO] Servicio de limpieza de oficinas municipales', 83000.00, '2026-05-22', '2026-11-18', 'critico', 40, 36, 3);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (41, '008/2026', '[EJEMPLO] Construcción de empedrado en calle principal', 457000.00, '2025-11-20', '2026-11-20', 'proximo_a_vencer', 41, 37, 4);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (42, '009/2026', '[EJEMPLO] Provisión de mobiliario para el centro de salud', 26000.00, '2026-05-29', '2026-11-25', 'proximo_a_vencer', 42, 36, 1);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (43, '010/2026', '[EJEMPLO] Supervisión técnica de obra vial', 134000.00, '2025-12-01', '2026-12-01', 'proximo_a_vencer', 43, 37, 2);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (44, '011/2026', '[EJEMPLO] Servicio de internet institucional', 95000.00, '2026-06-10', '2026-12-07', 'proximo_a_vencer', 34, 36, 3);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (45, '012/2026', '[EJEMPLO] Mejoramiento de plaza principal', 23400.00, '2025-12-11', '2026-12-11', 'proximo_a_vencer', 35, 37, 4);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (46, '013/2026', '[EJEMPLO] Consultoría de diseño de sistema de riego', 242000.00, '2026-06-29', '2026-12-26', 'vigente', 36, 36, 1);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (47, '014/2026', '[EJEMPLO] Provisión de uniformes para personal operativo', 61000.00, '2026-01-10', '2027-01-10', 'vigente', 37, 37, 2);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (48, '015/2026', '[EJEMPLO] Mantenimiento de vehículos municipales', 974000.00, '2026-08-13', '2027-02-09', 'vigente', 38, 36, 3);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (49, '016/2026', '[EJEMPLO] Construcción de muro de contención', 46500.00, '2026-03-11', '2027-03-11', 'vigente', 39, 37, 4);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (50, '017/2026', '[EJEMPLO] Servicio de vigilancia', 93000.00, '2026-10-12', '2027-04-10', 'vigente', 40, 36, 1);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (51, '018/2026', '[EJEMPLO] Adquisición de equipos de cómputo', 467000.00, '2026-05-10', '2027-05-10', 'vigente', 41, 37, 2);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (52, '019/2026', '[EJEMPLO] Ampliación de red de alcantarillado', 36000.00, '2027-01-10', '2027-07-09', 'vigente', 42, 36, 3);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (53, '020/2026', '[EJEMPLO] Consultoría de auditoría de procesos', 144000.00, '2026-09-07', '2027-09-07', 'vigente', 43, 37, 4);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (54, '021/2026', '[EJEMPLO] Provisión de combustible', 105000.00, '2027-05-15', '2027-11-11', 'vigente', 34, 36, 1);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (55, '022/2026', '[EJEMPLO] Construcción de sede social', 33400.00, '2026-01-25', '2027-01-25', 'renovado', 35, 37, 2);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (56, '023/2026', '[EJEMPLO] Servicio de fotocopiado', 252000.00, '2026-08-23', '2027-02-19', 'renovado', 36, 36, 3);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (57, '024/2026', '[EJEMPLO] Refacción del mercado central', 71000.00, '2026-05-30', '2027-05-30', 'terminado', 37, 37, 4);
INSERT INTO public.contrato (id_contrato, numero, objeto, monto, fecha_inicio, fecha_vencimiento, estado, id_contratista, id_responsable, id_tipo) VALUES (58, '025/2026', '[EJEMPLO] Provisión de materiales de construcción', 984000.00, '2026-09-22', '2027-03-21', 'terminado', 38, 36, 1);

-- Data for Name: alerta; Type: TABLE DATA; Schema: public; Owner: -

INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (34, 'vencido', 'Contrato 001/2026 ([EJEMPLO] Construcción de cancha polifuncional): venció el 27/09/2026. Requiere acción inmediata.', '2026-11-11 19:11:52.022626+00', 'sistema', false, 34);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (35, 'vencido', 'Contrato 002/2026 ([EJEMPLO] Provisión de material de escritorio): venció el 22/10/2026. Requiere acción inmediata.', '2026-11-11 19:11:52.029319+00', 'sistema', false, 35);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (36, 'vencido', 'Contrato 003/2026 ([EJEMPLO] Mantenimiento de alumbrado público): venció el 08/11/2026. Requiere acción inmediata.', '2026-11-11 19:11:52.035983+00', 'sistema', false, 36);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (37, 'garantia_35', 'Contrato 003/2026: la poliza de garantía venció hace 3 días (08/11/2026).', '2026-11-11 19:11:52.041108+00', 'sistema', false, 36);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (38, 'critico', 'Contrato 004/2026 ([EJEMPLO] Consultoría para estudio de factibilidad de agua potable): estado CRÍTICO, vence hoy (11/11/2026).', '2026-11-11 19:11:52.046625+00', 'sistema', false, 37);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (39, 'critico', 'Contrato 005/2026 ([EJEMPLO] Refacción de la unidad educativa): estado CRÍTICO, vence en 2 días (13/11/2026).', '2026-11-11 19:11:52.052893+00', 'sistema', false, 38);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (40, 'garantia_36', 'Contrato 005/2026: la boleta de garantía vence en 2 días (13/11/2026).', '2026-11-11 19:11:52.060561+00', 'sistema', false, 38);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (41, 'critico', 'Contrato 006/2026 ([EJEMPLO] Adquisición de luminarias LED): estado CRÍTICO, vence en 5 días (16/11/2026).', '2026-11-11 19:11:52.065862+00', 'sistema', false, 39);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (42, 'critico', 'Contrato 007/2026 ([EJEMPLO] Servicio de limpieza de oficinas municipales): estado CRÍTICO, vence en 7 días (18/11/2026).', '2026-11-11 19:11:52.072075+00', 'sistema', false, 40);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (43, 'aviso_15', 'Contrato 008/2026 ([EJEMPLO] Construcción de empedrado en calle principal): vence en 9 días (20/11/2026). Evalúe su renovación o cierre.', '2026-11-11 19:11:52.07854+00', 'sistema', false, 41);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (44, 'aviso_15', 'Contrato 009/2026 ([EJEMPLO] Provisión de mobiliario para el centro de salud): vence en 14 días (25/11/2026). Evalúe su renovación o cierre.', '2026-11-11 19:11:52.084739+00', 'sistema', false, 42);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (45, 'garantia_38', 'Contrato 009/2026: la boleta de garantía vence en 14 días (25/11/2026).', '2026-11-11 19:11:52.089888+00', 'sistema', false, 42);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (46, 'aviso_30', 'Contrato 010/2026 ([EJEMPLO] Supervisión técnica de obra vial): vence en 20 días (01/12/2026). Evalúe su renovación o cierre.', '2026-11-11 19:11:52.094847+00', 'sistema', false, 43);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (47, 'aviso_30', 'Contrato 011/2026 ([EJEMPLO] Servicio de internet institucional): vence en 26 días (07/12/2026). Evalúe su renovación o cierre.', '2026-11-11 19:11:52.100419+00', 'sistema', false, 44);
INSERT INTO public.alerta (id_alerta, nivel, mensaje, fecha_emision, canal, leida, id_contrato) VALUES (48, 'aviso_30', 'Contrato 012/2026 ([EJEMPLO] Mejoramiento de plaza principal): vence en 30 días (11/12/2026). Evalúe su renovación o cierre.', '2026-11-11 19:11:52.105804+00', 'sistema', false, 45);

-- Data for Name: auditoria; Type: TABLE DATA; Schema: public; Owner: -

INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (67, 'contratista', 'INSERT', 'Contratista Constructora Altiplano S.R.L. (ejemplo)', '2026-11-11 19:11:51.665536+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (68, 'contratista', 'INSERT', 'Contratista Servicios Andinos Ltda. (ejemplo)', '2026-11-11 19:11:51.6684+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (69, 'contratista', 'INSERT', 'Contratista Ingeniería y Obras Ingavi S.A. (ejemplo)', '2026-11-11 19:11:51.670335+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (70, 'contratista', 'INSERT', 'Contratista Provisiones del Sur S.R.L. (ejemplo)', '2026-11-11 19:11:51.672286+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (71, 'contratista', 'INSERT', 'Contratista Consultora Illimani (ejemplo)', '2026-11-11 19:11:51.674195+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (72, 'contratista', 'INSERT', 'Contratista Mantenimiento Técnico El Alto S.R.L. (ejemplo)', '2026-11-11 19:11:51.676072+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (73, 'contratista', 'INSERT', 'Contratista Suministros Viacha Ltda. (ejemplo)', '2026-11-11 19:11:51.678055+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (74, 'contratista', 'INSERT', 'Contratista Constructora Tiwanaku S.A. (ejemplo)', '2026-11-11 19:11:51.679911+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (75, 'contratista', 'INSERT', 'Contratista Consultores Asociados Titicaca (ejemplo)', '2026-11-11 19:11:51.681821+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (76, 'contratista', 'INSERT', 'Contratista Transportes y Equipos Aroma S.R.L. (ejemplo)', '2026-11-11 19:11:51.683684+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (77, 'contrato', 'INSERT', 'Contrato 001/2026 registrado', '2026-11-11 19:11:51.697357+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (78, 'contrato', 'INSERT', 'Contrato 002/2026 registrado', '2026-11-11 19:11:51.704526+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (79, 'contrato', 'INSERT', 'Contrato 003/2026 registrado', '2026-11-11 19:11:51.713089+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (80, 'contrato', 'INSERT', 'Contrato 004/2026 registrado', '2026-11-11 19:11:51.719895+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (81, 'contrato', 'INSERT', 'Contrato 005/2026 registrado', '2026-11-11 19:11:51.728556+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (82, 'contrato', 'INSERT', 'Contrato 006/2026 registrado', '2026-11-11 19:11:51.735609+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (83, 'contrato', 'INSERT', 'Contrato 007/2026 registrado', '2026-11-11 19:11:51.743908+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (84, 'contrato', 'INSERT', 'Contrato 008/2026 registrado', '2026-11-11 19:11:51.75097+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (85, 'contrato', 'INSERT', 'Contrato 009/2026 registrado', '2026-11-11 19:11:51.758841+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (86, 'contrato', 'INSERT', 'Contrato 010/2026 registrado', '2026-11-11 19:11:51.765812+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (87, 'contrato', 'INSERT', 'Contrato 011/2026 registrado', '2026-11-11 19:11:51.774068+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (88, 'contrato', 'INSERT', 'Contrato 012/2026 registrado', '2026-11-11 19:11:51.780663+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (89, 'contrato', 'INSERT', 'Contrato 013/2026 registrado', '2026-11-11 19:11:51.788638+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (90, 'contrato', 'INSERT', 'Contrato 014/2026 registrado', '2026-11-11 19:11:51.795478+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (91, 'contrato', 'INSERT', 'Contrato 015/2026 registrado', '2026-11-11 19:11:51.803626+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (92, 'contrato', 'INSERT', 'Contrato 016/2026 registrado', '2026-11-11 19:11:51.810184+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (93, 'contrato', 'INSERT', 'Contrato 017/2026 registrado', '2026-11-11 19:11:51.818533+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (94, 'contrato', 'INSERT', 'Contrato 018/2026 registrado', '2026-11-11 19:11:51.826007+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (95, 'contrato', 'INSERT', 'Contrato 019/2026 registrado', '2026-11-11 19:11:51.836318+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (96, 'contrato', 'INSERT', 'Contrato 020/2026 registrado', '2026-11-11 19:11:51.84432+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (97, 'contrato', 'INSERT', 'Contrato 021/2026 registrado', '2026-11-11 19:11:51.854673+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (98, 'contrato', 'INSERT', 'Contrato 022/2026 registrado', '2026-11-11 19:11:51.862468+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (99, 'contrato', 'INSERT', 'Contrato 023/2026 registrado', '2026-11-11 19:11:51.874146+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (100, 'contrato', 'INSERT', 'Contrato 024/2026 registrado', '2026-11-11 19:11:51.882642+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (101, 'contrato', 'INSERT', 'Contrato 025/2026 registrado', '2026-11-11 19:11:51.891738+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (102, 'contrato', 'UPDATE', 'Contrato 022/2026: estado vigente -> renovado', '2026-11-11 19:11:51.895311+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (103, 'contrato', 'UPDATE', 'Contrato 023/2026: estado vigente -> renovado', '2026-11-11 19:11:51.898593+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (104, 'contrato', 'UPDATE', 'Contrato 024/2026: estado vigente -> terminado', '2026-11-11 19:11:51.901781+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (105, 'contrato', 'UPDATE', 'Contrato 025/2026: estado vigente -> terminado', '2026-11-11 19:11:51.904792+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (106, 'seguimiento', 'INSERT', 'Seguimiento en contrato 001/2026', '2026-11-11 19:11:51.909322+00', 36);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (107, 'seguimiento', 'INSERT', 'Seguimiento en contrato 002/2026', '2026-11-11 19:11:51.913574+00', 37);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (108, 'seguimiento', 'INSERT', 'Seguimiento en contrato 004/2026', '2026-11-11 19:11:51.917655+00', 37);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (109, 'seguimiento', 'INSERT', 'Seguimiento en contrato 005/2026', '2026-11-11 19:11:51.921943+00', 36);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (110, 'seguimiento', 'INSERT', 'Seguimiento en contrato 009/2026', '2026-11-11 19:11:51.926165+00', 36);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (111, 'documento', 'INSERT', 'Documento «clausulas_ejemplo.txt» en contrato 004/2026', '2026-11-11 19:11:51.932583+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (112, 'documento', 'INSERT', 'Documento «acta_recepcion_ejemplo.docx» en contrato 005/2026', '2026-11-11 19:11:52.012971+00', 35);
INSERT INTO public.auditoria (id_log, tabla, operacion, detalle, fecha_hora, id_usuario) VALUES (113, 'alerta', 'REVISION', 'Revisión del 11/11/2026: 21 contratos, 0 estados actualizados, 15 alertas', '2026-11-11 19:11:52.13715+00', NULL);

-- Data for Name: garantia; Type: TABLE DATA; Schema: public; Owner: -

INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (34, 'boleta', '2026-10-07', 34);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (35, 'poliza', '2026-11-08', 36);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (36, 'boleta', '2026-11-13', 38);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (37, 'poliza', '2026-11-28', 40);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (38, 'boleta', '2026-11-25', 42);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (39, 'poliza', '2026-12-07', 44);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (40, 'boleta', '2027-01-05', 46);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (41, 'poliza', '2027-02-09', 48);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (42, 'boleta', '2027-04-10', 50);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (43, 'poliza', '2027-07-19', 52);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (44, 'boleta', '2027-11-11', 54);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (45, 'poliza', '2027-02-19', 56);
INSERT INTO public.garantia (id_garantia, tipo, fecha_vencimiento, id_contrato) VALUES (46, 'boleta', '2027-03-31', 58);

-- Data for Name: seguimiento; Type: TABLE DATA; Schema: public; Owner: -

INSERT INTO public.seguimiento (id_seguimiento, accion, fecha, id_contrato, id_usuario) VALUES (34, 'Se solicitó al contratista la ampliación de la garantía.', '2026-11-11 19:11:51.907221+00', 34, 36);
INSERT INTO public.seguimiento (id_seguimiento, accion, fecha, id_contrato, id_usuario) VALUES (35, 'Se consultó a jurídica sobre la renovación.', '2026-11-11 19:11:51.912036+00', 35, 37);
INSERT INTO public.seguimiento (id_seguimiento, accion, fecha, id_contrato, id_usuario) VALUES (36, 'Se coordinó reunión de cierre con la unidad solicitante.', '2026-11-11 19:11:51.916181+00', 37, 37);
INSERT INTO public.seguimiento (id_seguimiento, accion, fecha, id_contrato, id_usuario) VALUES (37, 'Se solicitó al contratista la ampliación de la garantía.', '2026-11-11 19:11:51.920434+00', 38, 36);
INSERT INTO public.seguimiento (id_seguimiento, accion, fecha, id_contrato, id_usuario) VALUES (38, 'Se solicitó al contratista la ampliación de la garantía.', '2026-11-11 19:11:51.924636+00', 42, 36);

-- Name: alerta_id_alerta_seq; Type: SEQUENCE SET; Schema: public; Owner: -

SELECT pg_catalog.setval('public.alerta_id_alerta_seq', 48, true);

-- Name: auditoria_id_log_seq; Type: SEQUENCE SET; Schema: public; Owner: -

SELECT pg_catalog.setval('public.auditoria_id_log_seq', 113, true);

-- Name: contratista_id_contratista_seq; Type: SEQUENCE SET; Schema: public; Owner: -

SELECT pg_catalog.setval('public.contratista_id_contratista_seq', 43, true);

-- Name: contrato_id_contrato_seq; Type: SEQUENCE SET; Schema: public; Owner: -

SELECT pg_catalog.setval('public.contrato_id_contrato_seq', 58, true);

-- Name: garantia_id_garantia_seq; Type: SEQUENCE SET; Schema: public; Owner: -

SELECT pg_catalog.setval('public.garantia_id_garantia_seq', 46, true);

-- Name: seguimiento_id_seguimiento_seq; Type: SEQUENCE SET; Schema: public; Owner: -

SELECT pg_catalog.setval('public.seguimiento_id_seguimiento_seq', 38, true);

-- Name: unidad_organizacional_id_unidad_seq; Type: SEQUENCE SET; Schema: public; Owner: -

SELECT pg_catalog.setval('public.unidad_organizacional_id_unidad_seq', 1, false);

-- Name: usuario_id_usuario_seq; Type: SEQUENCE SET; Schema: public; Owner: -

SELECT pg_catalog.setval('public.usuario_id_usuario_seq', 38, true);

-- PostgreSQL database dump complete


