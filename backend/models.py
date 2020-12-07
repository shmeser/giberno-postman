from django.contrib.gis.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    def get_nullable_fields(self):
        fields = self._meta.concrete_fields
        return [f.column for f in fields if getattr(f, 'blank', True) and getattr(f, 'null', True)]

    class Meta:
        abstract = True
