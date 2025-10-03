from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import User1, Farmer1, Consumer1, WebData
from rest_framework import serializers   # <-- this import is required

# class ConsumerGeoSerializer(GeoFeatureModelSerializer):
#     class Meta:
#         model = Consumer
#         geo_field = "geom"  # your PointField name
#         fields = ('id', 'name','data')  # fields to include in properties

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User1
       
        fields = '__all__'
        read_only_fields = ["id"]   # prevent client from sending UUID

        
class FarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer1
        read_only_fields = ['id']
        fields = '__all__'

class ConsumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumer1
        read_only_fields = ['id']
        fields = '__all__'

class WebDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebData
        fields = '__all__'

# 🔹 Serializer for user registration (using Django's default User model)
class RegisterSerializer(serializers.ModelSerializer):
    job = serializers.ChoiceField(choices=[('consumer', 'Consumer'), ('farmer', 'Farmer')], required=True)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)

    class Meta:
        model = User1
        fields = ['username', 'password', 'email', 'mobile', 'job', 'latitude', 'longitude']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        job = validated_data.pop('job', None)
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)

        user = User1.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )

        user.mobile = validated_data.get('mobile', '')
        user.job = job

        if latitude is not None and longitude is not None:
            user.latitude = latitude
            user.longitude = longitude

        user.save()
        return user