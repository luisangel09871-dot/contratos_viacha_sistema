"""Formularios Django: solo interpretan y limpian lo que escribe el usuario (adaptador de entrada).
Las reglas de negocio se validan en el dominio y los casos de uso."""
from django import forms

FECHA = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})


class AccesoForm(forms.Form):
    correo = forms.EmailField(label="Correo", widget=forms.EmailInput(attrs={"autocomplete": "username", "autofocus": True}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class ContratoForm(forms.Form):
    numero = forms.CharField(label="Número de contrato", max_length=30, help_text="Ejemplo: 045/2026")
    objeto = forms.CharField(label="Objeto del contrato", widget=forms.Textarea(attrs={"rows": 3}))
    id_tipo = forms.ChoiceField(label="Tipo de contrato")
    id_contratista = forms.ChoiceField(label="Contratista")
    id_responsable = forms.ChoiceField(label="Responsable del contrato")
    monto = forms.DecimalField(label="Monto (Bs)", min_value=0, max_digits=14, decimal_places=2)
    fecha_inicio = forms.DateField(label="Fecha de inicio", widget=FECHA)
    fecha_vencimiento = forms.DateField(label="Fecha de vencimiento", widget=FECHA)
    garantia_tipo = forms.ChoiceField(label="Garantía (opcional)", required=False,
                                      choices=[("", "Sin garantía"), ("boleta", "Boleta de garantía"), ("poliza", "Póliza")])
    garantia_vencimiento = forms.DateField(label="Vencimiento de la garantía", required=False, widget=FECHA)

    def __init__(self, *args, catalogos=None, con_garantia=True, **kwargs):
        super().__init__(*args, **kwargs)
        cat = catalogos or {"tipos": [], "contratistas": [], "responsables": []}
        self.fields["id_tipo"].choices = [(str(i), n) for i, n in cat["tipos"]]
        self.fields["id_contratista"].choices = [(str(c.id), c.razon_social) for c in cat["contratistas"]]
        self.fields["id_responsable"].choices = [(str(u.id), f"{u.nombre_completo} ({u.rol.etiqueta})") for u in cat["responsables"]]
        if not con_garantia:
            del self.fields["garantia_tipo"], self.fields["garantia_vencimiento"]

    def clean(self):
        datos = super().clean()
        if datos.get("garantia_tipo") and not datos.get("garantia_vencimiento"):
            self.add_error("garantia_vencimiento", "Indique la fecha de vencimiento de la garantía.")
        return datos


class FiltroForm(forms.Form):
    texto = forms.CharField(label="Buscar", required=False, max_length=100)
    estado = forms.ChoiceField(label="Estado", required=False, choices=[
        ("", "Todos"), ("vigente", "Vigente"), ("proximo_a_vencer", "Próximo a vencer"), ("critico", "Crítico"),
        ("vencido", "Vencido"), ("renovado", "Renovado"), ("terminado", "Terminado")])
    id_tipo = forms.ChoiceField(label="Tipo", required=False)
    id_contratista = forms.ChoiceField(label="Contratista", required=False)

    def __init__(self, *args, catalogos=None, **kwargs):
        super().__init__(*args, **kwargs)
        cat = catalogos or {"tipos": [], "contratistas": []}
        self.fields["id_tipo"].choices = [("", "Todos")] + [(str(i), n) for i, n in cat["tipos"]]
        self.fields["id_contratista"].choices = [("", "Todos")] + [(str(c.id), c.razon_social) for c in cat["contratistas"]]


class SeguimientoForm(forms.Form):
    accion = forms.CharField(label="Acción realizada", max_length=1000, widget=forms.Textarea(attrs={"rows": 2}))


class GarantiaForm(forms.Form):
    tipo = forms.ChoiceField(label="Tipo", choices=[("boleta", "Boleta de garantía"), ("poliza", "Póliza")])
    fecha_vencimiento = forms.DateField(label="Vence el", widget=FECHA)


class ContratistaForm(forms.Form):
    razon_social = forms.CharField(label="Razón social", max_length=200)
    nit = forms.CharField(label="NIT", max_length=20, required=False)
    correo_contacto = forms.EmailField(label="Correo de contacto", required=False)


class UsuarioForm(forms.Form):
    nombre = forms.CharField(label="Nombre completo", max_length=150)
    correo = forms.EmailField(label="Correo")
    rol = forms.ChoiceField(label="Rol", choices=[("funcionario", "Funcionario de contrataciones"),
                                                  ("responsable", "Responsable de contrato"),
                                                  ("autoridad", "Autoridad / unidad jurídica"),
                                                  ("administrador", "Administrador del sistema")])
    password = forms.CharField(label="Contraseña inicial", min_length=8, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))


class UmbralesForm(forms.Form):
    dias_proximo = forms.IntegerField(label="Próximo a vencer (hasta N días antes)", min_value=2, max_value=365)
    dias_critico = forms.IntegerField(label="Crítico (hasta N días antes)", min_value=0, max_value=60)
    aviso_1 = forms.IntegerField(label="Primer aviso (días antes)", min_value=2, max_value=365)
    aviso_2 = forms.IntegerField(label="Segundo aviso (días antes)", min_value=1, max_value=365)
