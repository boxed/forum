from hashlib import md5
from math import sqrt

from django.contrib.auth.models import User
from django.core import validators
from django.db import models


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)} {self.pk}:{self}'

    class Meta:
        abstract = True


class Room(Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    custom_data = models.CharField(max_length=1024, db_index=True, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/rooms/{self.pk}/'


class BinaryField(models.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators.append(validators.MaxLengthValidator(self.max_length * 2))

    def db_type(self, connection):
        assert connection.settings_dict['ENGINE'] == 'django.db.backends.mysql', 'VARBINARY is mysql only'
        return f'varbinary({str(self.max_length)})'


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    text = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    path = BinaryField(max_length=1000, db_index=True, null=True)
    visible = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    time_created = models.DateTimeField(auto_now_add=True)

    last_changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', null=True)
    last_changed_time = models.DateTimeField(auto_now=True)

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
