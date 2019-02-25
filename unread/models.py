from django.contrib.auth.models import User
from django.db import models


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)} {self.pk}:{self}'

    class Meta:
        abstract = True


class SystemTime(Model):
    data = models.BigIntegerField()
    time = models.DateTimeField()

    system = models.CharField(max_length=255)

    class Meta:
        unique_together = ('system', 'data')

    def __repr__(self):
        return f'SystemTime {self.system}/{self.data}: {self.time}'


class UserTime(Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    data = models.BigIntegerField()
    time = models.DateTimeField()

    system = models.CharField(max_length=255)

    class Meta:
        unique_together = ('user', 'system', 'data')

    def __repr__(self):
        return f'UserTime for {self.user} {self.system}/{self.data}: {self.time}'