from models import Strava
from rest_framework import serializers


class StravaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Strava
        fields = ('activity_id',
                  '_date',
                  'name',
                  'distance_miles',
                  'avg_power',
                  'moving_time_seconds',
                  'elevation_feet',
                  'kudos_count',
                  'kilojoules')
