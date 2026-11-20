"""Modelos Django = esquema de PostgreSQL. Viven SOLO en el adaptador de persistencia:
el dominio nunca los ve (los repositorios convierten entre modelo y entidad).
Los nombres de tabla coinciden con el Anexo C del informe."""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import F, Q


class RolModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_rol")
    nombre = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = "rol"


class UnidadModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_unidad")
    nombre = models.CharField(max_length=120)

    class Meta:
        db_table = "unidad_organizacional"


class GestorUsuarios(BaseUserManager):
    use_in_migrations = False

    def create_user(self, correo, password=None, **extra):
        if not correo:
            raise ValueError("El correo es obligatorio")
        usuario = self.model(correo=self.normalize_email(correo).lower(), **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario


class UsuarioModelo(AbstractBaseUser):
    id = models.AutoField(primary_key=True, db_column="id_usuario")
    rol = models.ForeignKey(RolModelo, on_delete=models.PROTECT, db_column="id_rol")
    unidad = models.ForeignKey(UnidadModelo, null=True, blank=True, on_delete=models.SET_NULL, db_column="id_unidad")
    nombre_completo = models.CharField(max_length=150)
    correo = models.EmailField(max_length=150, unique=True)
    password = models.CharField(max_length=255, db_column="password_hash")  # siempre un hash, nunca texto plano
    activo = models.BooleanField(default=True)

    USERNAME_FIELD = "correo"
    REQUIRED_FIELDS = ["nombre_completo"]
    objects = GestorUsuarios()

    @property
    def is_active(self):  # lo usa el sistema de autenticación de Django
        return self.activo

    class Meta:
        db_table = "usuario"


class ContratistaModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_contratista")
    razon_social = models.CharField(max_length=200)
    nit = models.CharField(max_length=20, unique=True, null=True, blank=True)
    correo_contacto = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "contratista"


class TipoContratoModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_tipo")
    nombre = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = "tipo_contrato"


class ContratoModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_contrato")
    numero = models.CharField(max_length=30, unique=True)
    objeto = models.TextField()
    tipo = models.ForeignKey(TipoContratoModelo, on_delete=models.PROTECT, db_column="id_tipo")
    contratista = models.ForeignKey(ContratistaModelo, on_delete=models.PROTECT, db_column="id_contratista")
    responsable = models.ForeignKey(UsuarioModelo, on_delete=models.PROTECT, db_column="id_responsable",
                                    related_name="contratos_a_cargo")
    monto = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_vencimiento = models.DateField(db_index=True)
    estado = models.CharField(max_length=20, default="registrado")

    class Meta:
        db_table = "contrato"
        constraints = [
            models.CheckConstraint(condition=Q(monto__gte=0), name="ck_contrato_monto"),
            models.CheckConstraint(condition=Q(fecha_vencimiento__gte=F("fecha_inicio")), name="ck_contrato_fechas"),
        ]


class GarantiaModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_garantia")
    contrato = models.ForeignKey(ContratoModelo, on_delete=models.CASCADE, db_column="id_contrato",
                                 related_name="garantias")
    tipo = models.CharField(max_length=40)
    fecha_vencimiento = models.DateField()

    class Meta:
        db_table = "garantia"


class AlertaModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_alerta")
    contrato = models.ForeignKey(ContratoModelo, on_delete=models.CASCADE, db_column="id_contrato",
                                 related_name="alertas")
    nivel = models.CharField(max_length=20)
    mensaje = models.TextField(blank=True, default="")
    fecha_emision = models.DateTimeField()
    canal = models.CharField(max_length=20)
    leida = models.BooleanField(default=False)

    class Meta:
        db_table = "alerta"
        indexes = [models.Index(fields=["contrato", "nivel"], name="ix_alerta_contrato_nivel")]


class SeguimientoModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_seguimiento")
    contrato = models.ForeignKey(ContratoModelo, on_delete=models.CASCADE, db_column="id_contrato",
                                 related_name="seguimientos")
    usuario = models.ForeignKey(UsuarioModelo, on_delete=models.PROTECT, db_column="id_usuario")
    accion = models.TextField()
    fecha = models.DateTimeField()

    class Meta:
        db_table = "seguimiento"


class AuditoriaModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_log")
    usuario = models.ForeignKey(UsuarioModelo, null=True, blank=True, on_delete=models.SET_NULL,
                                db_column="id_usuario")
    tabla = models.CharField(max_length=60)
    operacion = models.CharField(max_length=20)
    detalle = models.TextField(blank=True, default="")
    fecha_hora = models.DateTimeField()

    class Meta:
        db_table = "auditoria"


class DocumentoModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_documento")
    contrato = models.ForeignKey(ContratoModelo, on_delete=models.CASCADE, db_column="id_contrato",
                                 related_name="documentos")
    nombre_original = models.CharField(max_length=200)
    nombre_archivo = models.CharField(max_length=80, unique=True)
    tipo = models.CharField(max_length=10)
    tamano = models.IntegerField()
    subido_por = models.ForeignKey(UsuarioModelo, on_delete=models.PROTECT, db_column="subido_por")
    fecha = models.DateTimeField()
    texto_extraido = models.TextField(blank=True, default="")

    class Meta:
        db_table = "documento"


class ConsultaChatbotModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_consulta")
    usuario = models.ForeignKey(UsuarioModelo, on_delete=models.CASCADE, db_column="id_usuario")
    mensaje = models.TextField()
    intencion = models.CharField(max_length=40, null=True, blank=True)
    respuesta = models.TextField(blank=True, default="")
    adaptador = models.CharField(max_length=60, blank=True, default="")
    fecha_hora = models.DateTimeField()

    class Meta:
        db_table = "consulta_chatbot"


class UmbralModelo(models.Model):
    id = models.AutoField(primary_key=True, db_column="id_umbral")
    dias_proximo = models.IntegerField(default=30)
    dias_critico = models.IntegerField(default=7)
    aviso_1 = models.IntegerField(default=30)
    aviso_2 = models.IntegerField(default=15)

    class Meta:
        db_table = "umbral_alerta"
