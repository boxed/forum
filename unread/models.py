from django.contrib.auth.models import User
from django.db import models
from tri.token import TokenContainer, Token, TokenAttribute


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)} {self.pk}:{self}'

    class Meta:
        abstract = True


DATA_LENGTH = 512


class SystemTime(Model):
    system = models.CharField(max_length=255, db_index=True)
    data = models.BigIntegerField(db_index=True)
    identifier = models.CharField(max_length=DATA_LENGTH, db_index=True)
    time = models.DateTimeField()

    class Meta:
        unique_together = ('identifier',)

    def __repr__(self):
        return f'SystemTime {self.identifier}: {self.time}'


class UserTime(Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, db_index=True)
    system = models.CharField(max_length=255, db_index=True)
    identifier = models.CharField(max_length=DATA_LENGTH, db_index=True)
    data = models.BigIntegerField(db_index=True)
    time = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'identifier')

    def __repr__(self):
        return f'UserTime for {self.user} {self.identifier}: {self.time}'


class SubscriptionType(Token):
    name = TokenAttribute()
    display_name = TokenAttribute(value=lambda name, **_: name.title())


class SubscriptionTypes(TokenContainer):
    active = SubscriptionType()
    passive = SubscriptionType()


class Subscription(Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, db_index=True)
    system = models.CharField(max_length=255, db_index=True)
    data = models.BigIntegerField(db_index=True)
    identifier = models.CharField(max_length=DATA_LENGTH, db_index=True)
    # noinspection PyTypeChecker
    subscription_type = models.CharField(max_length=50, choices=[(x.name, x.display_name) for x in SubscriptionTypes], db_index=True)

    class Meta:
        unique_together = ('user', 'identifier',)
