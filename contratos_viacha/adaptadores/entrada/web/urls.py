from django.urls import path

from . import vistas as v

app_name = "web"
urlpatterns = [
    path("", v.panel, name="panel"),
    path("acceso/", v.acceso, name="acceso"),
    path("salir/", v.salir, name="salir"),
    path("healthz/", v.salud, name="salud"),
    path("contratos/", v.contratos_lista, name="contratos"),
    path("contratos/nuevo/", v.contrato_nuevo, name="contrato_nuevo"),
    path("contratos/<int:id_contrato>/", v.contrato_ficha, name="contrato_ficha"),
    path("contratos/<int:id_contrato>/editar/", v.contrato_editar, name="contrato_editar"),
    path("contratos/<int:id_contrato>/estado/", v.contrato_estado, name="contrato_estado"),
    path("contratos/<int:id_contrato>/garantia/", v.garantia_nueva, name="garantia_nueva"),
    path("contratos/<int:id_contrato>/seguimiento/", v.seguimiento_nuevo, name="seguimiento_nuevo"),
    path("contratos/<int:id_contrato>/documento/", v.documento_subir, name="documento_subir"),
    path("documentos/<int:id_documento>/descargar/", v.documento_descargar, name="documento_descargar"),
    path("contratistas/", v.contratistas, name="contratistas"),
    path("alertas/", v.alertas, name="alertas"),
    path("alertas/<int:id_alerta>/leida/", v.alerta_leida, name="alerta_leida"),
    path("reportes/", v.reportes, name="reportes"),
    path("administracion/usuarios/", v.usuarios, name="usuarios"),
    path("administracion/usuarios/<int:id_usuario>/rol/", v.usuario_rol, name="usuario_rol"),
    path("administracion/usuarios/<int:id_usuario>/activo/", v.usuario_activo, name="usuario_activo"),
    path("administracion/umbrales/", v.umbrales, name="umbrales"),
    path("administracion/auditoria/", v.auditoria, name="auditoria"),
    path("chatbot/consultar/", v.chatbot_consultar, name="chatbot_consultar"),
    path("chatbot/subir/", v.chatbot_subir, name="chatbot_subir"),
]
