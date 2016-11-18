from __future__ import unicode_literals

from django.db import models

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datawarehouse.settings")

class Strava(models.Model):
    """
    Model which holds all of my cycling data
    """
    activity_id = models.IntegerField(primary_key=True)
    name = models.TextField()
    _date = models.DateField()
    distance_miles = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    avg_power = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    moving_time_seconds = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    elapsed_time_seconds = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    kudos_count = models.IntegerField(null=True, blank=True)
    elevation_feet = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    kilojoules = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    country = models.TextField(null=True)
    city = models.TextField(null=True)
    latitude = models.FloatField(null=True)
    longitude = models.TextField(null=True)

