from datetime import datetime

# TODO:
#  - Subscriptions
#    - Active
#    - Passive
#  - Better name for "system"
#  - Should systems be models in the DB and not just stringly typed?
#  - Do I need multi level unread? Maybe just system/user is ok?


# noinspection PyShadowingBuiltins
from typing import Optional


def get_time_for_system(*, id, system: str, time: Optional[datetime] = None):
    from .models import SystemTime
    if time is None:
        time = datetime(2001, 1, 1)
    return SystemTime.objects.update_or_create(data=id, system=system, defaults=dict(time=time)).time


# noinspection PyShadowingBuiltins
def set_time_for_system(*, id, system: str, time: datetime):
    from .models import SystemTime
    SystemTime.objects.update_or_create(data=id, system=system, defaults=dict(time=time))


# noinspection PyShadowingBuiltins
def get_time(*, user, system: str, id: int) -> datetime:
    from .models import UserTime
    return UserTime.objects.get_or_create(user=user, data=id, system=system, defaults=dict(time=datetime(2001, 1, 1)))[0].time


# noinspection PyShadowingBuiltins
def set_time(*, user, system: str, id: int, time: datetime) -> None:
    from .models import UserTime
    UserTime.objects.update_or_create(user=user, data=id, system=system, defaults=dict(time=time))


def is_unread(*, user, system: str, id: int):
    return get_time(user=user, system=system, id=id) < get_time_for_system(system=system, id=id)
