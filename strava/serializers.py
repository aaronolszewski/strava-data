from models import Strava
from rest_framework import serializers


class StravaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Strava
        fields = ('activity_id',
                  'name',
                  '_date',
                  'distance_miles',
                  'city',
                  'country',
                  'kilojoules')
