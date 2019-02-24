from django.contrib.auth.models import User
from django.db import models


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)} {self.pk}:{self}'

    class Meta:
        abstract = True


class Time(Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    data = models.BigIntegerField()
    time = models.DateTimeField()

    system = models.CharField(max_length=255)

    class Meta:
        unique_together = ('user', 'system', 'data')

    def __repr__(self):
        return f'Time for {self.user} {self.system}/{self.data}: {self.time}'
