from django.db import models


class Event(models.Model):
    baby_name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=200)
    event_subtype = models.CharField(max_length=200)
    value = models.IntegerField(default=0)
    dt = models.DateTimeField('date of occurrence')
    objects = models.Manager()
