"""Excepciones del dominio. Python puro: no depende de Django ni de librerías externas."""


class ErrorDeDominio(Exception):
    """Base de los errores de negocio."""


class ErrorValidacion(ErrorDeDominio):
    """Datos que no cumplen una regla del dominio."""


class PermisoDenegado(ErrorDeDominio):
    """El usuario no tiene permiso para la operación."""


class NoEncontrado(ErrorDeDominio):
    """El recurso solicitado no existe."""


class CredencialesInvalidas(ErrorDeDominio):
    """Usuario o contraseña incorrectos."""
