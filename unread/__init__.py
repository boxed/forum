from datetime import datetime

# TODO:
#  - Subscriptions
#    - Active
#    - Passive
#  - Better name for "system"
#  - Should systems be models in the DB and not just stringly typed?
#  - Do I need multi level unread? Maybe just system/user is ok?


# noinspection PyShadowingBuiltins
from itertools import groupby
from typing import Optional, List, Dict, Tuple

DEFAULT_TIME = datetime(2001, 1, 1)


def get_time_by_data_and_system(*, id: int, system: str, time: Optional[datetime] = None):
    from .models import SystemTime
    if time is None:
        time = DEFAULT_TIME
    return SystemTime.objects.get_or_create(data=id, system=system, defaults=dict(time=time))[0].time


def get_times(*, ids: List[Tuple[str, int]]):
    from .models import SystemTime

    time_by_system_by_data = {}
    for system, ids_ in groupby(ids, key=lambda x: x[0]):
        time_by_system_by_data[system] = get_times_by_system(system=system, ids=[x[1] for x in ids_])

    return time_by_system_by_data


def get_times_by_system(*, system: str, ids: List[int]) -> Dict[int, datetime]:
    from .models import SystemTime
    times = SystemTime.objects.filter(data__in=ids).filter(system=system)
    time_by_data = {x.data: x.time for x in times}
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


def get_times_for_user(*, user, ids: List[Tuple[str, int]]):
    from .models import UserTime

    time_by_system_by_data = {}
    for system, ids_ in groupby(ids, key=lambda x: x[0]):
        time_by_system_by_data[system] = get_times_for_user_by_system(user=user, system=system, ids=[x[1] for x in ids_])

    return time_by_system_by_data


def get_times_for_user_by_system(*, user, system: str, ids: List[int]):
    from .models import UserTime
    times = UserTime.objects.filter(user=user, data__in=ids, system=system)
    time_by_data = {x.data: x.time for x in times}
    return {
        id: time_by_data.get(id, DEFAULT_TIME)
        for id in ids
    }


# noinspection PyShadowingBuiltins
def set_time(*, user, system: str, id: int, time: datetime) -> None:
    from .models import UserTime
    UserTime.objects.update_or_create(user=user, data=id, system=system, defaults=dict(time=time))


def is_unread(*, user, system: str, id: int):
    return get_time(user=user, system=system, id=id) < get_time_by_data_and_system(system=system, id=id)


def unread_items(*, user):
    from unread.models import Subscription

    subscriptions = Subscription.objects.filter(user=user)
    s = list(subscriptions)
    ids = [(x.system, x.data) for x in s]
    system_time_by_id_by_system = get_times(ids=ids)
    user_time_by_id_by_system = get_times_for_user(user=user, ids=ids)

    return {
        system: {
            id: True
            for id, time in
            system_time_by_id.items()
            if user_time_by_id_by_system[system].get(id, DEFAULT_TIME) < time
        }
        for system, system_time_by_id in
        system_time_by_id_by_system.items()
    }
    #
    # return [
    #     (system, id)
    #     for system, id in ids
    #     if user_time_by_id_by_system[system].get(id, DEFAULT_TIME) < system_time_by_id_by_system[system].get(id, DEFAULT_TIME)
    # ]
