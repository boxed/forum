from datetime import datetime

# TODO:
#  - Better name for "system"
#  - Better name for "data"
#  - Should systems be models in the DB and not just stringly typed?
#  - Do I need multi level unread? Maybe just system/user is ok?


# noinspection PyShadowingBuiltins
from itertools import groupby
from typing import Optional, List, Dict, Tuple

DEFAULT_TIME = datetime(2001, 1, 1)


def get_time_by_data_and_system(*, data: int, system: str, time: Optional[datetime] = None):
    from .models import SystemTime
    if time is None:
        time = DEFAULT_TIME
    return SystemTime.objects.get_or_create(data=data, system=system, defaults=dict(time=time))[0].time


def get_times(*, data_list: List[Tuple[str, int]]):
    from .models import SystemTime

    time_by_system_by_data = {}
    for system, ids_ in groupby(data_list, key=lambda x: x[0]):
        time_by_system_by_data[system] = get_times_by_system(system=system, data_list=[x[1] for x in ids_])

    return time_by_system_by_data


def get_times_by_system(*, system: str, data_list: List[int]) -> Dict[int, datetime]:
    from .models import SystemTime
    times = SystemTime.objects.filter(data__in=data_list).filter(system=system)
    time_by_data = {x.data: x.time for x in times}
    return {
        id: time_by_data.get(id, DEFAULT_TIME)
        for id in data_list
    }


# noinspection PyShadowingBuiltins
def set_time_for_system(*, data, system: str, time: datetime):
    from .models import SystemTime
    SystemTime.objects.update_or_create(data=data, system=system, defaults=dict(time=time))


# noinspection PyShadowingBuiltins
def get_time(*, user, system: str, data: int) -> datetime:
    from .models import UserTime
    return UserTime.objects.get_or_create(user=user, data=data, system=system, defaults=dict(time=DEFAULT_TIME))[0].time


def get_times_for_user(*, user, data_list: List[Tuple[str, int]]):
    from .models import UserTime

    time_by_system_by_data = {}
    for system, ids_ in groupby(data_list, key=lambda x: x[0]):
        time_by_system_by_data[system] = get_times_for_user_by_system(user=user, system=system, data_list=[x[1] for x in ids_])

    return time_by_system_by_data


def get_times_for_user_by_system(*, user, system: str, data_list: List[int]):
    from .models import UserTime
    times = UserTime.objects.filter(user=user, data__in=data_list, system=system)
    time_by_data = {x.data: x.time for x in times}
    return {
        id: time_by_data.get(id, DEFAULT_TIME)
        for id in data_list
    }


# noinspection PyShadowingBuiltins
def set_time(*, user, system: str, data: int, time: datetime) -> None:
    from .models import UserTime
    UserTime.objects.update_or_create(user=user, data=data, system=system, defaults=dict(time=time))


def is_unread(*, user, system: str, data: int):
    return get_time(user=user, system=system, data=data) < get_time_by_data_and_system(system=system, data=data)


def unread_items(*, user):
    from unread.models import Subscription

    subscriptions = Subscription.objects.filter(user=user)
    s = list(subscriptions)
    ids = [(x.system, x.data) for x in s]
    system_time_by_id_by_system = get_times(data_list=ids)
    user_time_by_id_by_system = get_times_for_user(user=user, data_list=ids)

    foo = {
        system: {
            id: True
            for id, time in
            system_time_by_id.items()
            if user_time_by_id_by_system[system].get(id, DEFAULT_TIME) <= time
        }
        for system, system_time_by_id in
        system_time_by_id_by_system.items()
    }
    return {k: v for k, v in foo.items() if v}


def is_subscribed(*, user, system: str, data: int) -> bool:
    from unread.models import Subscription
    return Subscription.objects.filter(user=user, system=system, data=data).exists()


def subscribe(*, user, system: str, data: int, subscription_type: str):
    from unread.models import Subscription
    Subscription.objects.create(user=user, system=system, data=data, subscription_type=subscription_type)


def unsubscribe(*, user, system: str, data: int, subscription_type: str):
    from unread.models import Subscription
    Subscription.objects.filter(user=user, system=system, data=data, subscription_type=subscription_type).delete()
