from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import User1, Farmer1, Consumer1, WebData,Commodity,DtProduce,DamageCrop
from rest_framework import serializers   # <-- this import is required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import uuid
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

class CommoditySerializer(serializers.ModelSerializer):
    class Meta:
        model = Commodity
       
        fields = '__all__'
        
class DtProduceSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField()
    class Meta:
        model = DtProduce
        fields = '__all__'
        
#  Serializer for user registration ( User1 model)
class RegisterSerializer(serializers.ModelSerializer):
    job = serializers.ChoiceField(choices=[('consumer', 'Consumer'), ('farmer', 'Farmer'),('retailer', 'Retailer')], required=True)
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)

    class Meta:
        model = User1
        fields = ['username', 'password', 'email', 'mobile', 'job', 'latitude', 'longitude']
        extra_kwargs = {'password': {'write_only': True}}
    
    # ---------------------------
    # FIELD-LEVEL VALIDATION
    # ---------------------------

    def validate_username(self, value):
        if not value:
            raise serializers.ValidationError("Username cannot be empty.")

        if User1.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")

        return value

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format.")

        if User1.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")

        return value

    def validate_mobile(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Mobile number must contain only digits.")

        if len(value) != 10:
            raise serializers.ValidationError("Mobile number must be 10 digits.")

        if User1.objects.filter(mobile=value).exists():
            raise serializers.ValidationError("Mobile number already registered.")

        return value
    # ---------------------------
    # OBJECT-LEVEL VALIDATION
    # ---------------------------

    def validate(self, data):
        lat = data.get("latitude")
        lon = data.get("longitude")

        if lat is None or lon is None:
            raise serializers.ValidationError(
                {"location": "Location permission required. Allow location and try again."}
            )

        return data

    # ---------------------------
    # CREATE USER
    # ---------------------------

    def create(self, validated_data):
        job = validated_data.pop('job')
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        mobile = validated_data.pop("mobile")
        email = validated_data.pop("email")      # <-- FIX #1
        password = validated_data.pop("password")  # <-- FIX #2

        user = User1.objects.create_user(
            id=str(uuid.uuid4()),
            username=validated_data['username'],
            email=email,
            password=password
            
        )

        user.mobile = mobile
        user.job = job
        user.latitude = latitude
        user.longitude = longitude


        user.save()
        return user
    
class DamageCropSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamageCrop
        fields = "__all__"