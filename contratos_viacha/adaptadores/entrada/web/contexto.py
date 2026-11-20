"""Context processor: datos del usuario para el menú de todas las páginas."""
from contratos_viacha.dominio import permisos
from contratos_viacha.adaptadores.entrada.web import vistas


def contexto_web(request):
    if not request.user.is_authenticated:
        return {}
    a = vistas.actor(request)
    return {
        "actor": a,
        "puede_editar": permisos.puede_editar_contratos(a),
        "puede_reportes": permisos.puede_ver_reportes(a),
        "es_admin": permisos.es_administrador(a),
        "alertas_pendientes": len(vistas.servicios().seguimiento.alertas(a, solo_no_leidas=True)),
    }
