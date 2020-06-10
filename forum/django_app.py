from django.apps import AppConfig
from iommi.style import (
    Style,
    register_style,
)
from iommi.style_base import base


class ForumConfig(AppConfig):
    name = 'forum'

    def ready(self):
        register_style(
            'forum',
            Style(
                base,
                Form__attrs__class__form=True,
                Field__attrs__class__field=True,
            )
        )
