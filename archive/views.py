from os import listdir
from pathlib import Path

from iommi import (
    Column,
    Table,
)


def index(request):
    return Table(
        columns__name=Column(),
        rows=Path('/storage').glob('*'),
    )
