from decimal import Decimal

from django import template

from contratos_viacha.aplicacion.casos_de_uso._comun import etiqueta_dias, fmt_monto

register = template.Library()


@register.filter
def bs(valor):
    try:
        return fmt_monto(Decimal(valor))
    except Exception:
        return "—"


@register.filter
def dias_texto(dias):
    return etiqueta_dias(int(dias))


@register.filter
def nivel_texto(nivel):
    if nivel.startswith("garantia"):
        return "Garantía por vencer"
    return {"aviso_30": "Aviso a 30 días", "aviso_15": "Aviso a 15 días",
            "critico": "Crítico", "vencido": "Vencido"}.get(nivel, nivel)


@register.filter
def tamano(n):
    n = int(n)
    return f"{n/1024:.0f} KB" if n < 1024 * 1024 else f"{n/1024/1024:.1f} MB"


@register.filter
def get_item(d, k):
    return d.get(k, 0)
