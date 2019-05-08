from django.contrib.auth.models import User
from django.db import models


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)} {self.pk}:{self}'

    class Meta:
        abstract = True


class ResetCode(Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=1024)

    def __str__(self):
        return self.code
