from datetime import datetime

# TODO:
#  - Subscriptions
#    - Active
#    - Passive
#  - Better name for "system"
#  - Should systems be models in the DB and not just stringly typed?
#  - Do I need multi level unread? Maybe just system/user is ok?


# noinspection PyShadowingBuiltins
from typing import Optional, List

DEFAULT_TIME = datetime(2001, 1, 1)


def get_time_for_system(*, id, system: str, time: Optional[datetime] = None):
    from .models import SystemTime
    if time is None:
        time = DEFAULT_TIME
    return SystemTime.objects.get_or_create(data=id, system=system, defaults=dict(time=time))[0].time


def get_times_for_system(*, system: str, ids: List[int]):
    from .models import SystemTime
    time_by_data = {x.data: x.time for x in SystemTime.objects.filter(data__in=ids, system=system)}
    return {
        id: time_by_data.get(id, DEFAULT_TIME)
        for id in ids
    }


# noinspection PyShadowingBuiltins
def set_time_for_system(*, id, system: str, time: datetime):
    from .models import SystemTime
    SystemTime.objects.update_or_create(data=id, system=system, defaults=dict(time=time))


# noinspection PyShadowingBuiltins
def get_time(*, user, system: str, id: int) -> datetime:
    from .models import UserTime
    return UserTime.objects.get_or_create(user=user, data=id, system=system, defaults=dict(time=DEFAULT_TIME))[0].time


def get_times_for_user(*, user, system: str, ids: List[int]):
    from .models import UserTime
    time_by_data = {x.data: x.time for x in UserTime.objects.filter(user=user, data__in=ids, system=system)}
    return {
        id: time_by_data.get(id, DEFAULT_TIME)
        for id in ids
    }


# noinspection PyShadowingBuiltins
def set_time(*, user, system: str, id: int, time: datetime) -> None:
    from .models import UserTime
    UserTime.objects.update_or_create(user=user, data=id, system=system, defaults=dict(time=time))


def is_unread(*, user, system: str, id: int):
    return get_time(user=user, system=system, id=id) < get_time_for_system(system=system, id=id)
