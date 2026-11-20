import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contratos_viacha.configuracion.settings")
application = get_wsgi_application()
