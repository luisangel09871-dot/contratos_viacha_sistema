"""Solo para pruebas: PBKDF2 con pocas iteraciones para que la suite corra rápido.
El algoritmo es el mismo que en producción (pbkdf2_sha256); solo cambia el costo."""
from django.contrib.auth.hashers import PBKDF2PasswordHasher


class RapidoPBKDF2(PBKDF2PasswordHasher):
    iterations = 1000
