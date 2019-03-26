from dataclasses import dataclass
from datetime import datetime

from typing import List, Dict, Any

from tri.token import Token, TokenAttribute, TokenContainer

DEFAULT_TIME = datetime(2001, 1, 1)


def get_time(*, identifier: str):
    from .models import SystemTime
    try:
        return SystemTime.objects.get(identifier=identifier).time
    except SystemTime.DoesNotExist:
        return DEFAULT_TIME


def get_times(*, identifiers: List[str]) -> Dict[str, datetime]:
    from .models import SystemTime

    time_by_identifier = {x.identifier: x.time for x in SystemTime.objects.filter(identifier__in=identifiers)}

    return {
        identifier: time_by_identifier.get(identifier, DEFAULT_TIME)
        for identifier in identifiers
    }


def set_time(*, identifier: str = None, time: datetime): #, item_id: Any = None, namespace: str = None):
    # assert identifier or (item_id and namespace), "Either use the identifier parameter, or both namespace and item_id"
    # if identifier is None:
    #     identifier = f'{namespace}:{item_id}'
    from .models import SystemTime
    SystemTime.objects.update_or_create(identifier=identifier, defaults=dict(time=time))


def get_user_time(*, user, identifier: str) -> datetime:
    from .models import UserTime
    try:
        return UserTime.objects.get(user=user, identifier=identifier).time
    except UserTime.DoesNotExist:
        return DEFAULT_TIME


def get_user_times(*, user, identifiers: List[str]) -> Dict[str, datetime]:
    from .models import UserTime

    time_by_identifier = {x.identifier: x.time for x in UserTime.objects.filter(user=user, identifier__in=identifiers)}

    return {
        identifier: time_by_identifier.get(identifier, DEFAULT_TIME)
        for identifier in identifiers
    }


def set_user_time(*, user, identifier: str, time: datetime) -> None:
    from .models import UserTime
    UserTime.objects.update_or_create(user=user, identifier=identifier, defaults=dict(time=time))


def is_unread(*, user, identifier: str) -> bool:
    return get_user_time(user=user, identifier=identifier) <= get_time(identifier=identifier)


def is_unread_(user_time, item_time):
    return user_time <= item_time


# Don't think this thing is really needed... subscription_data does all of it better?
def unread_items(*, user):
    from unread.models import Subscription

    identifiers = Subscription.objects.filter(user=user).values_list('identifier', flat=True)
    system_time_by_identifier = get_times(identifiers=identifiers)
    user_time_by_identifier = get_user_times(user=user, identifiers=identifiers)

    return {
        identifier: is_unread_(user_time=user_time_by_identifier[identifier], item_time=system_time_by_identifier[identifier])
        for identifier in identifiers
    }

class SubscriptionType(Token):
    name = TokenAttribute()
    display_name = TokenAttribute(value=lambda name, **_: name.title())


class SubscriptionTypes(TokenContainer):
    active = SubscriptionType()
    passive = SubscriptionType()


@dataclass
class SubscriptionData:
    is_unread: bool
    user_time: datetime
    item_time: datetime
    subscription_type: SubscriptionType


def subscription_data(*, user) -> Dict[str, SubscriptionData]:
    from unread.models import Subscription

    foo = Subscription.objects.filter(user=user).values_list('identifier', 'subscription_type')
    identifiers = [x[0] for x in foo]
    subscription_type_by_identifier = {x[0]: x[1] for x in foo}
    item_time_by_identifier = get_times(identifiers=identifiers)
    user_time_by_identifier = get_user_times(user=user, identifiers=identifiers)

    return {
        identifier: SubscriptionData(
            is_unread=is_unread_(user_time=user_time_by_identifier[identifier], item_time=item_time_by_identifier[identifier]),
            user_time=user_time_by_identifier[identifier],
            item_time=item_time_by_identifier[identifier],
            subscription_type=subscription_type_by_identifier[identifier],
        )
        for identifier in identifiers
    }


def is_subscribed(*, user, identifier: str) -> bool:
    from unread.models import Subscription
    return Subscription.objects.filter(user=user, identifier=identifier).exists()


def subscribe(*, user, identifier: str, subscription_type: str):
    from unread.models import Subscription
    unsubscribe(user=user, identifier=identifier)
    Subscription.objects.create(user=user, identifier=identifier, subscription_type=subscription_type)


def unsubscribe(*, user, identifier: str):
    from unread.models import Subscription
    Subscription.objects.filter(user=user, identifier=identifier).delete()
