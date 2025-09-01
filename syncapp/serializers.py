from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Consumer

class ConsumerGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Consumer
        geo_field = "geom"  # your PointField name
        fields = ('id', 'name','data')  # fields to include in properties
