import pytest
from freezegun import freeze_time

from tests.helpers import (
    req,
)
from tests.models import Foo
from unread import (
    unread_handling,
    UnreadData,
    DEFAULT_TIME,
    get_user_time,
    get_unread_identifier,
)

pytestmark = [pytest.mark.django_db]


@unread_handling(Foo)
def view_function(request, foo, unread_data):
    return unread_data, foo


def test_unread_basic(admin_user):
    with freeze_time('2019-04-17') as t:
        request = req('get')
        request.user = admin_user
        unread_data, foo = view_function(request, foo=Foo.objects.create(name='foo'))

        assert unread_data == UnreadData(is_subscribed=False, unread2_time=DEFAULT_TIME, user_time=DEFAULT_TIME, unread_identifier=f'tests/foo:{foo.pk}')

        now = t()
        unread_data, foo = view_function(request, foo=foo)

        assert unread_data == UnreadData(is_subscribed=False, unread2_time=now, user_time=now, unread_identifier=f'tests/foo:{foo.pk}')

        t.tick()
        last_time = now
        now = t()
        assert last_time != now

        request = req('get', time=last_time.isoformat())
        request.user = admin_user

        unread_data, foo = view_function(request, foo=foo)
        assert unread_data == UnreadData(is_subscribed=False, unread2_time=last_time, user_time=last_time, unread_identifier=f'tests/foo:{foo.pk}')
        assert get_user_time(user=admin_user, identifier=get_unread_identifier(foo)) == now

        # Test unread_from_here
        request = req('get', unread_from_here=last_time.isoformat())
        request.user = admin_user
        unread_data, foo = view_function(request, foo=foo)
        assert unread_data == UnreadData(is_subscribed=False, unread2_time=last_time, user_time=last_time, unread_identifier=f'tests/foo:{foo.pk}')
        assert get_user_time(user=admin_user, identifier=get_unread_identifier(foo)) == last_time
