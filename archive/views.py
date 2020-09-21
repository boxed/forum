from pathlib import Path

from django.conf import settings
from django.http import FileResponse
from django.utils.safestring import mark_safe
from iommi import (
    Column,
    Table,
)


def index(request, path):
    assert '..' not in path
    p = Path(settings.ARCHIVE_PATH) / path
    if p.is_file():
        return FileResponse(open(p, 'rb'), filename=p.name)
    rows = [
        x
        for x in p.glob('*')
        if not x.name.startswith('.')
    ]
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
    )
