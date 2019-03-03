"""
WSGI config for forum2 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from forum2 import CursorDebugWrapper

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forum2.settings')

from django.conf import settings

if getattr(settings, "REPLACE_CURSOR_DEBUG_WRAPPER", True):
    import django.db.backends.utils
    django.db.backends.utils.CursorDebugWrapper = CursorDebugWrapper


application = get_wsgi_application()
