from strava.models import Strava
from rest_framework.generics import ListAPIView
from strava.serializers import StravaSerializer


class StravaView(ListAPIView):
    """
    API endpoint for viewing Strava Data.
    """
    model = Strava
    serializer_class = StravaSerializer

    def get_queryset(self):
        queryset = self.model.objects.all()
        return queryset
