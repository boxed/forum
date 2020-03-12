from django.apps import AppConfig
from iommi.style import (
    Style,
    register_style,
)
from iommi import style


class ForumConfig(AppConfig):
    name = 'forum'

    def ready(self):
        register_style(
            'forum',
            Style(
                style.base,
                Form__attrs__class__form=True,
                Field__attrs__class__field=True,
            )
        )
