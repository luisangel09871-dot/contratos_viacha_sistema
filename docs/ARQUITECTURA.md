# Arquitectura hexagonal del sistema

## Idea central
El **dominio** (entidades y reglas de vencimiento) está en el centro y no conoce a Django, a PostgreSQL, al correo ni a Gemini.
Todo lo que está afuera se conecta mediante **puertos** (interfaces) y **adaptadores** (implementaciones concretas).
Las dependencias de código apuntan siempre hacia el dominio.

```
        ADAPTADORES DE ENTRADA                                   ADAPTADORES DE SALIDA
  vistas web ──┐                                                ┌── repositorios PostgreSQL (ORM)
  chatbot HTTP ┼─► PUERTOS DE ENTRADA ─► CASOS DE USO ─► PUERTOS DE SALIDA ─┼── correo SMTP
  comando diario ┘      (aplicacion/)      │   ▲          (aplicacion/)     ├── almacén de archivos
                                           ▼   │                           ├── lector PDF/DOCX
                                        DOMINIO (entidades, reglas,        ├── Gemini (modelo de lenguaje)
                                        permisos; Python puro)             ├── clasificador de intenciones
                                                                           └── reloj (real / falso)
```

## Puertos de entrada → casos de uso → adaptadores primarios
| Puerto de entrada | Caso de uso (`aplicacion/casos_de_uso/`) | Adaptador primario |
|---|---|---|
| GestionarContratos | `gestionar_contratos.py` | Vistas web |
| ConsultarVencimientos | `consultar_vencimientos.py` | Vistas web y chatbot |
| RegistrarSeguimiento | `registrar_seguimiento.py` | Vistas web |
| EjecutarRevisionDiaria | `revisar_vencimientos.py` | Comando `ejecutar_revision_diaria` |
| AdministrarUsuarios | `administrar_usuarios.py` | Vistas web (acceso, usuarios, umbrales, bitácora) |
| SubirDocumento / ConsultarDocumentos | `documentos.py` | Vistas web y subida desde el chat |
| ConsultarPorChatbot | `consultar_por_chatbot.py` | Endpoints `/chatbot/consultar/` y `/chatbot/subir/` |

## Puertos de salida → adaptadores secundarios
| Puerto de salida | Adaptador de producción | Doble de prueba |
|---|---|---|
| RepositorioContratos, Contratistas, TiposContrato, Garantias, Alertas, Seguimientos, Usuarios, Documentos, Umbrales, ConsultasChatbot | `adaptadores/salida/persistencia/repositorios.py` (PostgreSQL) | `pruebas/dobles.py` (memoria) |
| RegistroAuditoria | `RegistroAuditoriaORM` (tabla `auditoria`) | `Auditoria` (memoria) |
| Transaccion | `TransaccionORM` (`transaction.atomic`) | `Transaccion` (sin efecto) |
| RelojDelSistema | `reloj.RelojReal` | `RelojFalso` / `RelojPuro` |
| NotificadorCorreo | `correo.NotificadorSMTP` | `NotificadorSimulado` / `Notificador` |
| AlmacenDocumentos | `almacen.AlmacenLocal` | `AlmacenEnMemoria` / `Almacen` |
| ExtractorTexto | `extractor.ExtractorArchivos` (pypdf, python-docx) | `Extractor` |
| ModeloDeLenguaje | `gemini.AdaptadorGemini` | `ModeloFalso` |
| ClasificadorIntenciones | `clasificador.ClasificadorCompuesto` (reglas + modelo de apoyo) | (mismo, con `ModeloFalso`) |

## Decisiones de diseño que conviene explicar
1. **El dominio no pide la fecha al sistema operativo**: la recibe por el puerto `RelojDelSistema`. Así se prueba qué pasa
   con un contrato que vence en exactamente 7 días, sin esperar una semana.
2. **El chatbot no toca tablas ni archivos**: llama casos de uso, que validan permisos. Una pregunta mal entendida no puede
   exponer información fuera de lo que el usuario puede ver. Esto incluye los documentos.
3. **El modelo de lenguaje solo redacta**: fechas, estados y plazos salen siempre de las reglas. Si el modelo falla, el
   chatbot responde con plantillas (adaptador registrado en `consulta_chatbot.adaptador`).
4. **Las alertas son idempotentes** (`dominio/reglas_vencimiento.py::nivel_alerta_pendiente`): no se duplican si el motor
   corre dos veces, y si un día no corrió, se pone al día con la alerta más urgente.
5. **Los permisos viven en los casos de uso y en `dominio/permisos.py`**, no en las vistas: cualquier puerta de entrada
   (web, chatbot, comando) queda protegida igual.
6. **Un solo punto de ensamblaje**: `composicion.py` decide qué tecnología implementa cada puerto.

## Reglas de negocio (propuesta a validar con el GAM Viacha)
| Estado | Días hasta el vencimiento | Alerta |
|---|---|---|
| Vigente | más de 30 | ninguna |
| Próximo a vencer | de 30 a 8 | aviso a los 30 y a los 15 días |
| Crítico | de 7 a 0 | una por día |
| Vencido | menos de 0 | una sola vez |
| Renovado / Terminado | los fija una persona | ninguna |

Los umbrales son configurables por el administrador (pantalla «Umbrales»). Cada garantía genera además un aviso cuando
faltan 15 días o menos (el segundo umbral).
