from datetime import datetime


def get_time_for_system(*, id, system: str, time: datetime):
    from .models import SystemTime
    SystemTime.objects.update_or_create(data=id, system=system, defaults=dict(time=time))


def set_time_for_system(*, id, system: str, time: datetime):
    from .models import SystemTime
    SystemTime.objects.update_or_create(data=id, system=system, defaults=dict(time=time))


def get_time(*, user, system: str, id: int) -> datetime:
    from .models import UserTime
    return UserTime.objects.get_or_create(user=user, data=id, system=system, defaults=dict(time=datetime(2001, 1, 1)))[0].time


def set_time(*, user, system: str, id: int, time: datetime) -> None:
    from .models import UserTime
    UserTime.objects.update_or_create(user=user, data=id, system=system, defaults=dict(time=time))
