from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from forum.models import Room


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)} {self.pk}:{self}'

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Project(Model):
    name = models.CharField(max_length=255)

    def get_absolute_url(self):
        return f'/issues/projects/{self}/'

    class Meta:
        ordering = ('name',)


class PropertyGroup(Model):
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=255)


class Issue(Model):
    name = models.CharField(max_length=255, db_index=True)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    comments = models.ForeignKey(Room, on_delete=models.CASCADE, null=True)  # this will only be null during issue creation

    time_created = models.DateTimeField(auto_now_add=True)
    last_changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', null=True)
    last_changed_time = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return f'/issues/projects/{self.project}/issues/{self.pk}/'

    class Meta:
        ordering = ('pk',)


@receiver(pre_delete, sender=Issue)
def remove_room(instance, **_):
    if instance.comments:
        instance.comments.delete()


class UserProperty(Model):
    name = models.CharField(max_length=255, db_index=True)
    issue = models.ForeignKey(Issue, on_delete=models.PROTECT, related_name='user_properties')
    data = models.ForeignKey(User, on_delete=models.PROTECT)

    time_created = models.DateTimeField(auto_now_add=True)
    last_changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', null=True)
    last_changed_time = models.DateTimeField(auto_now=True)


class TextProperty(Model):
    name = models.CharField(max_length=255, db_index=True)
    issue = models.ForeignKey(Issue, on_delete=models.PROTECT, related_name='text_properties')
    data = models.CharField(max_length=255, db_index=True)

    time_created = models.DateTimeField(auto_now_add=True)
    last_changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', null=True)
    last_changed_time = models.DateTimeField(auto_now=True)


class LongTextProperty(Model):
    name = models.CharField(max_length=255, db_index=True)
    issue = models.ForeignKey(Issue, on_delete=models.PROTECT, related_name='long_text_properties')
    data = models.TextField()

    time_created = models.DateTimeField(auto_now_add=True)
    last_changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', null=True)
    last_changed_time = models.DateTimeField(auto_now=True)
