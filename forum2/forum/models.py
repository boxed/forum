from django.db import models


class Area(models.Model):
    name = models.CharField(max_length=255)


class User(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Message(models.Model):
    area = models.ForeignKey(Area, on_delete=models.PROTECT)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.PROTECT)
    path = models.BinaryField(max_length=1024, db_index=True)
    visible = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timecreated = models.DateTimeField()
    words = models.IntegerField()

    last_changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    last_changed_time = models.DateTimeField()

    def __repr__(self):
        return f'<Message: {self.pk}>'

    class Meta:
        ordering = ('path',)

    @property
    def indent(self):
        return len(self.path) // 8

    @property
    def indent_px(self):
        return self.indent * 20
