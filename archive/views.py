from os import listdir

from iommi import (
    Column,
    Table,
)


def index(request):
    return Table(
        columns__name=Column(),
        rows=listdir('/storage'),
    )
