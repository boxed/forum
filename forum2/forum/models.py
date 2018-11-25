from django.contrib.auth.models import User
from django.db import models


class HackySingleSignOn(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    session_key = models.CharField(max_length=40)


class Time(models.Model):
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


class Area(models.Model):
    name = models.CharField(max_length=255)
    mode = models.CharField(max_length=255)
    description = models.TextField()


class Message(models.Model):
    area = models.ForeignKey(Area, on_delete=models.PROTECT)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.PROTECT)
    path = models.BinaryField(max_length=1024, db_index=True)
    visible = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    time_created = models.DateTimeField()
    words = models.IntegerField()

    last_changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    last_changed_time = models.DateTimeField()

    has_replies = models.BooleanField(default=False)

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
