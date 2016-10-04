from strava.models import Strava
from rest_framework import viewsets
from strava.serializers import StravaSerializer


class StravaViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing Strava Data.
    """
    queryset = Strava.objects.all()
    serializer_class = StravaSerializer
    lookup_field = 'activity_id'
