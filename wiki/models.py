from django.db import models


class Model(models.Model):
    def __repr__(self):
        return f'{type(self)} {self.pk}:{self}'

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ('name', )

    def get_unread_identifier(self):
        return f'wiki/{self._meta.verbose_name}:{self.pk}'


class Context(Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    custom_data = models.CharField(max_length=255, db_index=True, null=True, blank=True)

    def get_absolute_url(self):
        return f'/wiki/{self.name}/'


class Document(Model):
    context = models.ForeignKey(Context, on_delete=models.PROTECT)
    # This is the current name, so can change
    name = models.CharField(max_length=127, db_index=True)
    custom_data = models.CharField(max_length=127, db_index=True, null=True, blank=True)

    class Meta:
        unique_together = ('context', 'name')

    @staticmethod
    def decode_url_dependencies():
        return ['context']

    def get_absolute_url(self):
        return f'/wiki/{self.context.name}/{self.name}/'


class DocumentVersion(Model):
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name='versions')
    name = models.CharField(max_length=255, db_index=True)
    version = models.IntegerField()  # strictly not needed, but makes for a nicer UX than using the pk
    changed_time = models.DateTimeField(auto_now_add=True)
    content = models.TextField(blank=True)
    custom_data = models.CharField(max_length=255, db_index=True, null=True, blank=True)

    def get_absolute_url(self):
        return f'/wiki/{self.document.context.name}/{self.document.name}/{self.pk}/'
