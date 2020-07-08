from django.contrib.auth.models import User
from django.db import models
from . import SubscriptionTypes


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)} {self.pk}:{self}'

    def __str__(self):
        # noinspection PyUnresolvedReferences
        return self.name

    class Meta:
        abstract = True


# This is what we expect from a thing that can be unread. You don't have to inherit from this class, but you should have these fields (last_changed_by isn't used by the unread app, but it's polite to keep track of)
class UnreadModel(Model):
    time_created = models.DateTimeField(auto_now_add=True)
    last_changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', null=True)
    last_changed_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


DATA_LENGTH = 255


class SystemTime(Model):
    identifier = models.CharField(max_length=DATA_LENGTH, db_index=True)
    time = models.DateTimeField()

    class Meta:
        unique_together = ('identifier',)

    def __repr__(self):
        return f'SystemTime {self.identifier}: {self.time}'


class UserTime(Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, db_index=True)
    identifier = models.CharField(max_length=DATA_LENGTH, db_index=True)
    time = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'identifier')

    def __repr__(self):
        return f'UserTime for {self.user} {self.identifier}: {self.time}'


class Subscription(Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, db_index=True)
    identifier = models.CharField(max_length=DATA_LENGTH, db_index=True)
    # noinspection PyTypeChecker
    subscription_type = models.CharField(max_length=50, choices=[(x.name, x.display_name) for x in SubscriptionTypes], db_index=True)

    class Meta:
        unique_together = ('user', 'identifier',)
