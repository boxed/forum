from django.contrib.auth.models import User
from django.db import transaction, connection, IntegrityError

from forum.models import bytes_from_int, Message, Room
from unread import set_time_for_system
from unread.models import SystemTime, Subscription, SubscriptionTypes


def update_batch(qs):
    count = 0
    for instance in qs:
        if not instance.path:
            if instance.parent:
                instance.path = instance.parent.path + bytes_from_int(instance.pk)
            else:
                instance.path = bytes_from_int(instance.pk)

            instance.save()
        if instance.parent and not instance.parent.has_replies:
            Message.objects.filter(pk=instance.parent.pk).update(has_replies=True)  # Don't use normal save() to avoid the auto_add field update

        count += 1
    return count



@transaction.atomic
def update_message_path():
    update_batch(Message.objects.filter(parent=None))
    from django.db.models import Q
    while update_batch(Message.objects.filter(path=None).filter(Q(parent=None) | Q(parent__path__isnull=False))):
        pass


def import_from_skforum():
    cursor = connection.cursor()
    # for table in ['forum_message', 'forum_room', 'unread_usertime', 'unread_systemtime']:
    #     cursor.execute(f'truncate {table}')

    import_users()
    import_rooms()
    import_messages()
    import_times()
    import_subscriptions()
    update_message_path()
    fix_broken_last_changed_timestamps()
    update_room_times()


def import_users():
    cursor = connection.cursor()
    cursor.execute('insert into auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) select id, password, NOW(), 0, name, "", "", email, 0, 1, NOW() from forum.users')


def import_rooms():
    cursor = connection.cursor()
    cursor.execute('insert into forum_room (id, name, description) select id, name, "" from forum.areas')


def import_messages():
    cursor = connection.cursor()
    cursor.execute("""
    insert into forum_message (text, room_id, id, user_id, last_changed_time, last_changed_by_id, path, parent_id, visible, has_replies, time_created)

    select CONCAT(Subject, '\n', Body), Area, ID, User, LastChanged, LastChangedUser, NULL, Parent, visible, 0, Timecreated 
    from forum.messages
    where Area in (select id from forum_room)
    order by ID
    """)


def import_times():
    from unread.models import UserTime
    UserTime.objects.all().delete()

    cursor = connection.cursor()
    cursor.execute('select `user`, `data`, `time` from forum.times where system = "0"')

    for row in cursor.fetchall():
        try:
            if row[0] is None:
                SystemTime.objects.create(data=row[1], system='forum.room', time=row[3])
            else:
                UserTime.objects.create(user_id=row[0], data=row[1], system='forum.room', time=row[2])
        except Exception as e:
            print(e)


def import_subscriptions():
    from collections import defaultdict

    cursor = connection.cursor()
    cursor.execute('select id, AreaGroup from forum.areas')

    areas_by_areagroup = defaultdict(set)
    for area, areagroup in cursor.fetchall():
        areas_by_areagroup[areagroup].add(area)

    cursor.execute('select * from forum.areahotlist')

    data = {0: {}, 1: {}}

    for user, area, areagroup, system in cursor.fetchall():
        data[system].setdefault(user, dict(areas=set(), areagroups=set()))
        if area:
            data[system][user]['areas'].add(area)
        else:
            assert areagroup
            data[system][user]['areagroups'].add(areagroup)

    for system, foo in data.items():
        for user, bar in foo.items():
            areas = bar['areas']
            areagroups = bar['areagroups']

            subscriptions = set()

            for areagroup in areagroups:
                areas_for_this_areagroup = areas_by_areagroup[areagroup] & areas
                areas -= areas_for_this_areagroup
                subscriptions |= areas_by_areagroup[areagroup] - areas_for_this_areagroup

            subscriptions |= areas

            for room_pk in subscriptions:
                try:
                    Room.objects.get(pk=room_pk)
                    User.objects.get(pk=user)

                    Subscription.objects.create(
                        user_id=user,
                        system='forum.room',
                        data=room_pk,
                        subscription_type=SubscriptionTypes.active if system == 0 else SubscriptionTypes.passive
                    )
                except Room.DoesNotExist:
                    print(f'invalid room pk {room_pk}')
                except User.DoesNotExist:
                    print(f'invalid user pk {room_pk}')
                except IntegrityError:
                    pass


def fix_broken_last_changed_timestamps():
    cursor = connection.cursor()
    cursor.execute('update forum_message set last_changed_time = time_created')


def update_room_times():
    for room in Room.objects.all():
        try:
            last_time = Message.objects.filter(room=room).order_by('-last_changed_time')[0].last_changed_time
            set_time_for_system(id=room.pk, system='forum.room', time=last_time)
        except IndexError:
            pass
