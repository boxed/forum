import functools
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Dict,
    List,
)

from tri_token import (
    Token,
    TokenAttribute,
    TokenContainer,
)

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


def set_time(*, identifier: str = None, time: datetime):
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

    foo = Subscription.objects.filter(user=user).order_by('identifier').values_list('identifier', 'subscription_type')
    identifiers = [x[0] for x in foo]
    subscription_type_by_identifier = {x[0]: x[1] for x in foo}
    item_time_by_identifier = get_times(identifiers=identifiers)
    user_time_by_identifier = get_user_times(user=user, identifiers=identifiers)

    def split_identifier(identifier):
        prefix, _, data = identifier.partition(':')
        assert not data.endswith('/')
        return prefix, data

    return {
        split_identifier(identifier): SubscriptionData(
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


@dataclass
class UnreadData:
    is_subscribed: bool
    user_time: datetime
    unread2_time: datetime
    unread_identifier: str

    def is_unread(self, obj_timestamp):
        if not isinstance(obj_timestamp, datetime):
            obj_timestamp = get_time(identifier=obj_timestamp.get_unread_identifier())
        return obj_timestamp >= self.user_time

    def is_unread2(self, obj_timestamp):
        if not isinstance(obj_timestamp, datetime):
            obj_timestamp = get_time(identifier=obj_timestamp.get_unread_identifier())
        return obj_timestamp >= self.unread2_time and not self.is_unread(obj_timestamp)


def get_unread_identifier(obj):
    model = type(obj)
    model_name = model._meta.verbose_name.replace(' ', '_')
    module_name = model.__module__.replace('.models', '')
    return f'{module_name}/{model_name}:{obj.pk}'


def unread_handling(model):
    """
    Decorator to handle unread handling. Note that this requires that you've already decoded the model coming in. You can do that with @decode_url.
    """
    model_name = model._meta.verbose_name.replace(' ', '_')

    def unread_handling_factory(f):
        @functools.wraps(f)
        def unread_handling_wrapper(request, **kwargs):
            obj = kwargs[model_name]

            unread_identifier = get_unread_identifier(obj)
            user_time = get_user_time(user=request.user, identifier=unread_identifier)

            if 'time' in request.GET:
                unread2_time = datetime.fromisoformat(request.GET['time'])
            else:
                unread2_time = datetime.now()

            # NOTE: there's a set_user_time at the very bottom of this function
            if 'unread_from_here' in request.GET:
                user_time = datetime.fromisoformat(request.GET['unread_from_here'])

            if user_time < unread2_time:
                unread2_time = user_time

            unread_data = UnreadData(
                is_subscribed=is_subscribed(user=request.user, identifier=unread_identifier),
                user_time=user_time,
                unread2_time=unread2_time,
                unread_identifier=unread_identifier,
            )

            r = f(request=request, unread_data=unread_data, **kwargs)

            if 'unread_from_here' not in request.GET:
                user_time = datetime.now()

            set_user_time(user=request.user, identifier=unread_identifier, time=user_time)

            return r

        return unread_handling_wrapper

    return unread_handling_factory
