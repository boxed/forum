from hashlib import md5

from django.contrib.auth.models import User
from django.core import validators
from django.db import models
from iommi import register_factory

from unread.models import UnreadModel


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)} {self.pk}:{self}'

    class Meta:
        abstract = True

    def get_unread_identifier(self):
        return f'wiki/context/{self._meta.verbose_name}:{self.pk}'


class Room(Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    custom_data = models.CharField(max_length=1024, db_index=True, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/rooms/{self.pk}/'

    def get_unread_id(self):
        return f'forum/room:{self.pk}'


class BinaryField(models.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators.append(validators.MaxLengthValidator(self.max_length * 2))

    def db_type(self, connection):
        assert connection.settings_dict['ENGINE'] == 'django.db.backends.mysql', 'VARBINARY is mysql only'
        return f'varbinary({str(self.max_length)})'


register_factory(BinaryField, factory=None)


class Message(UnreadModel):
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='messages')
    text = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='replies')
    path = BinaryField(max_length=1000, db_index=True, null=True)
    visible = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='messages')

    has_replies = models.BooleanField(default=False)

    custom_data = models.CharField(max_length=1024, db_index=True, null=True, blank=True)

    def __repr__(self):
        return f'<Message: {self.pk}>'

    def get_absolute_url(self):
        return f'/rooms/{self.room.pk}/message/{self.pk}/'

    class Meta:
        ordering = ('path',)

    @property
    def indent(self):
        return (len(self.path) // 8) - 1

    @property
    def indent_rem(self):
        return self.indent * 2 + 3

    @property
    def gravatar_url(self):
        return f'https://www.gravatar.com/avatar/{md5(self.user.email.encode()).hexdigest()}?d=identicon'


def bytes_from_int(i):
    return i.to_bytes(length=64 // 8, byteorder='big')
