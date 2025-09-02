from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import User1, Farmer1, Consumer1, WebData,Consumer
from rest_framework import serializers   # <-- this import is required

class ConsumerGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Consumer
        geo_field = "geom"  # your PointField name
        fields = ('id', 'name','data')  # fields to include in properties

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User1
        fields = '__all__'

class FarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer1
        fields = '__all__'

class ConsumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumer1
        fields = '__all__'

class WebDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebData
        fields = '__all__'