from mimetypes import guess_type
from pathlib import Path

from django.conf import settings
from django.http import FileResponse
from django.utils.safestring import mark_safe
from iommi import (
    Column,
    Table,
    Action,
)


def is_image(name):
    type, _ = guess_type(name)
    if type is not None and type.startswith('image/'):
        return True
    else:
        return False


def index(request, path=''):
    assert '..' not in path

    p = Path(settings.ARCHIVE_PATH) / path
    if p.is_file():
        return FileResponse(open(p, 'rb'), filename=p.name)
    rows = [
        x
        for x in p.glob('*')
        if not x.name.startswith('.')
    ]

    if request.GET.get('gallery') is not None:
        images = [
            x
            for x in rows
            if is_image(x)
        ]
        return Table.div(
            rows=sorted(images, key=lambda x: x.name.lower()),
            page_size=None,
            columns__name=Column(cell__format=lambda row, **_: mark_safe(f'<img src="{row.name}" style="max-width: 100%">'))
        )

    return Table(
        columns=dict(
            icon=Column(
                display_name='',
                header__attrs__style__width='25px',
                attr=None,
                cell__format=lambda row, **_: mark_safe('<i class="far fa-folder"></i>') if row.is_dir() else ''
            ),
            name=Column(
                cell__url=lambda row, **_: f'{row.name}/' if row.is_dir() else row.name,
            ),
        ),
        page_size=None,
        rows=sorted(rows, key=lambda x: x.name.lower()),
        actions__gallery=Action(attrs__href='?gallery')
    )
