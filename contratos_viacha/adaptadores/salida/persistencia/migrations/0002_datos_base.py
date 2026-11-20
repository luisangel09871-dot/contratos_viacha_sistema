from django.db import migrations

ROLES = ["funcionario", "responsable", "autoridad", "administrador"]
TIPOS = ["Obras", "Bienes", "Servicios generales", "Consultoría"]


def cargar(apps, schema_editor):
    Rol, Tipo, Umbral = apps.get_model("persistencia", "RolModelo"), apps.get_model("persistencia", "TipoContratoModelo"), apps.get_model("persistencia", "UmbralModelo")
    for n in ROLES:
        Rol.objects.get_or_create(nombre=n)
    for n in TIPOS:
        Tipo.objects.get_or_create(nombre=n)
    Umbral.objects.get_or_create(id=1, defaults=dict(dias_proximo=30, dias_critico=7, aviso_1=30, aviso_2=15))


class Migration(migrations.Migration):
    dependencies = [("persistencia", "0001_initial")]
    operations = [migrations.RunPython(cargar, migrations.RunPython.noop)]
