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

# 🔹 Serializer for user registration (using Django's default User model)
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User1
        fields = ['username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User1.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )