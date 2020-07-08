from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from forum.models import Room
from unread.models import (
    UnreadModel,
    Model,
)


class Project(Model):
    name = models.CharField(max_length=255)

    def get_absolute_url(self):
        return f'/issues/projects/{self}/'

    class Meta:
        ordering = ('name',)


class PropertyGroup(Model):
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=255)


class Issue(UnreadModel):
    name = models.CharField(max_length=255, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    comments = models.ForeignKey(Room, on_delete=models.CASCADE, null=True)  # this will only be null during issue creation

    def get_absolute_url(self):
        return f'/issues/projects/{self.project}/issues/{self.pk}/'

    class Meta:
        ordering = ('pk',)


@receiver(pre_delete, sender=Issue)
def remove_room(instance, **_):
    if instance.comments:
        instance.comments.delete()


class UserProperty(UnreadModel):
    name = models.CharField(max_length=255, db_index=True)
    issue = models.ForeignKey(Issue, on_delete=models.PROTECT, related_name='user_properties')
    data = models.ForeignKey(User, on_delete=models.PROTECT)


class TextProperty(UnreadModel):
    name = models.CharField(max_length=255, db_index=True)
    issue = models.ForeignKey(Issue, on_delete=models.PROTECT, related_name='text_properties')
    data = models.CharField(max_length=255, db_index=True)


class LongTextProperty(UnreadModel):
    name = models.CharField(max_length=255, db_index=True)
    issue = models.ForeignKey(Issue, on_delete=models.PROTECT, related_name='long_text_properties')
    data = models.TextField()
