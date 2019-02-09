from django.contrib.auth.models import User
from django.db import models


class HackySingleSignOn(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    session_key = models.CharField(max_length=40)


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)}:{self}'

    class Meta:
        abstract = True


class Time(Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    data = models.BigIntegerField()
    time = models.DateTimeField()

    system = models.CharField(max_length=255)
    # area
    # planning
    # welcome
    # wiki
    # polls
    # tasks
    # calendar
    class Meta:
        unique_together = ('user', 'system', 'data')

    def __repr__(self):
        return f'Time for {self.user} {self.system}/{self.data}: {self.time}'


class Area(Model):
    name = models.CharField(max_length=255)
    mode = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/areas/{self.pk}/'


class Message(models.Model):
    area = models.ForeignKey(Area, on_delete=models.PROTECT)
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    path = models.BinaryField(max_length=1024, db_index=True)
    visible = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    time_created = models.DateTimeField(auto_now_add=True)
    words = models.IntegerField()

    last_changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', null=True)
    last_changed_time = models.DateTimeField(auto_now=True)

    has_replies = models.BooleanField(default=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.path is None:
            self.path = self.parent.path + bytes_from_int(self.pk)
        super(Message, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def __repr__(self):
        return f'<Message: {self.pk}>'

    def get_absolute_url(self):
        return f'/areas/{self.area.pk}/message/{self.pk}/'

    class Meta:
        ordering = ('path',)

    @property
    def indent(self):
        return (len(self.path) // 8) - 1

    @property
    def indent_px(self):
        return self.indent * 20


def bytes_from_int(i):
    return i.to_bytes(length=64 // 8, byteorder='big')
