import logging, json, requests, uuid
from datetime import datetime
from bs4 import BeautifulSoup

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt  # ← import here

from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Consumer1, User1, Farmer1, WebData, Commodity
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    FarmerSerializer,
    ConsumerSerializer,
    WebDataSerializer,
    
)
from django.utils.decorators import method_decorator
from django.db.models import Max, Q

logger = logging.getLogger(__name__)
User = get_user_model()

# ---------------------------------------------------------------------
# ViewSets (protected with JWT)
# ---------------------------------------------------------------------

class UserViewSet(viewsets.ModelViewSet):
    queryset = User1.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class FarmerViewSet(viewsets.ModelViewSet):
    queryset = Farmer1.objects.all()
    serializer_class = FarmerSerializer
    permission_classes = [IsAuthenticated]


class ConsumerViewSet(viewsets.ModelViewSet):
    queryset = Consumer1.objects.all()
    serializer_class = ConsumerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Example: only show consumers since 30 Aug 2025
        filter_date = timezone.make_aware(datetime(2025, 8, 30))
        return Consumer1.objects.filter(date__gte=filter_date)


class WebDataViewSet(viewsets.ModelViewSet):
    queryset = WebData.objects.all()
    serializer_class = WebDataSerializer
    permission_classes = [IsAuthenticated]


# ---------------------------------------------------------------------
# Register new user
# ---------------------------------------------------------------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


# ---------------------------------------------------------------------
# Login API (JWT)
# ---------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    """
    Login with username + password and return JWT tokens
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"status": "error", "message": "Username and password required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)
    if not user:
        return Response(
            {"status": "error", "message": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    refresh = RefreshToken.for_user(user)
    return Response({
        "status": "success",
        "message": "Login successful",
        "user_id": user.id,
        "username": user.username,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })


# ---------------------------------------------------------------------
# Profile API (Protected)
# ---------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    return Response({
        "message": "Authenticated successfully",
        "username": request.user.username,
    })


# ---------------------------------------------------------------------
# Consumers GeoJSON (Protected)
# ---------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def consumers_geojson(request):
    cutoff_date = timezone.make_aware(datetime(2024, 1, 1))
    consumers = Consumer1.objects.filter(date__gte=cutoff_date)

    features = []
    for c in consumers:
        if c.latitude and c.longitude:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [c.longitude, c.latitude],
                },
                "properties": {
                    "id": c.id,
                    "name": c.commodity,
                    "commodity": c.commodity,
                    "date": c.date.isoformat() if c.date else None,
                    "buyingprice": c.buyingprice,
                    "quantitybought": c.quantitybought,
                    "unit": c.unit,
                },
            })

    geojson = {
        "message": f"You are authenticated, {request.user.username}",
        "type": "FeatureCollection",
        "features": features,
    }
    return JsonResponse(geojson)


# ---------------------------------------------------------------------
# Agrowon Prices Scraper
# ---------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([AllowAny])  # public endpoint
def agrowon_prices(request):
    """
    Scrape Agrowon market prices and return as JSON
    """
    url = "https://www.agrowon.com/agriculture-latest-news"  # change to actual mandi prices page
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return Response({"status": "error", "message": "Failed to fetch data"}, status=500)

        soup = BeautifulSoup(resp.content, "html.parser")
        prices = []

        # Example parsing logic: adjust selectors based on actual Agrowon HTML
        rows = soup.select("table tbody tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                commodity = cols[0].get_text(strip=True)
                market = cols[1].get_text(strip=True)
                price = cols[2].get_text(strip=True)
                prices.append({
                    "commodity": commodity,
                    "market": market,
                    "price": price,
                })

        return Response({
            "status": "success",
            "count": len(prices),
            "prices": prices,
        })

    except Exception as e:
        logger.error(f"Agrowon scrape failed: {e}")
        return Response(
            {"status": "error", "message": "Scraping failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def webdata_prices(request):
    commodity_name = request.GET.get('commodity')
    if not commodity_name:
        return JsonResponse({'error': 'Commodity parameter required'}, status=400)

    today = timezone.localdate()

    # 1️⃣ Try today's data
    data_qs = WebData.objects.filter(
        commodity__iexact=commodity_name,
        date__date=today
    )

    # 2️⃣ If not found, try alias from Commodity table
    if not data_qs.exists():
        commodity_obj = Commodity.objects.filter(name__iexact=commodity_name).first()
        if commodity_obj and commodity_obj.alias_marathi:
            data_qs = WebData.objects.filter(
                commodity__iexact=commodity_obj.alias_marathi,
                date__date=today
            )

    # 3️⃣ If still not found, fetch latest available date
    if not data_qs.exists():
        latest_date = WebData.objects.filter(
            Q(commodity__iexact=commodity_name) |
            Q(commodity__iexact=getattr(commodity_obj, "alias_marathi", None))
        ).aggregate(Max("date"))["date__max"]

        if not latest_date:
            return JsonResponse({'error': 'No data found'}, status=404)

        data_qs = WebData.objects.filter(date=latest_date).filter(
            Q(commodity__iexact=commodity_name) |
            Q(commodity__iexact=getattr(commodity_obj, "alias_marathi", None))
        )

    # 4️⃣ Serialize results
    results = [
        {
            'commodity': data.commodity,
            'apmc': data.apmc,
            'variety': data.variety,
            'minprice': data.minprice,
            'maxprice': data.maxprice,
            'modalprice': data.modalprice,
            'unit': data.unit,
            'date': data.date.isoformat() if data.date else None,
            'is_latest': (data.date.date() != today)  # flag if not today's
        }
        for data in data_qs
    ]

    return JsonResponse(results, safe=False)

@csrf_exempt
def api_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            user = User1(
                id=str(uuid.uuid4()),  # ✅ text UUID
                username=data['username'],
                email=data.get('email', ''),
                mobile=data.get('mobile', ''),
                job=data.get('job', ''),
                latitude=data.get('latitude'),
                longitude=data.get('longitude')
            )
            user.set_password(data['password'])
            user.save()

            return JsonResponse({
                "status": "success",
                "message": "User registered successfully",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "mobile": user.mobile,
                    "job": user.job,
                    "latitude": user.latitude,
                    "longitude": user.longitude
                }
            })
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
@api_view(["GET"])
@permission_classes([AllowAny])
def debug_headers(request):
    return Response({"headers": dict(request.headers)})


# ✅ Custom token serializer (optional: include username in response)
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # add custom claims
        token["username"] = user.username
        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# ✅ Optional: Test endpoint
@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
# @method_decorator(csrf_exempt, name='dispatch')

def whoami(request):
    return Response({
        "id": request.user.id,
        "username": request.user.username,
        "auth": str(type(request.auth))  # shows if JWT or session
    })
# api for whole sale market prices
@api_view(['GET'])
@permission_classes([AllowAny])
def webdata_prices_public(request):
    commodity_name = request.GET.get('commodity')
    if not commodity_name:
        return Response({'error': 'Commodity parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    date_str = request.GET.get('date')
    if date_str:
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({'error': 'Invalid date format, use YYYY-MM-DD'}, status=400)
    else:
        query_date = timezone.localdate()

    today = timezone.localdate()

    # First, try today's data for exact commodity
    data_qs = WebData.objects.filter(
        commodity__iexact=commodity_name,
        date__date=today
    )

    # If no data today, try alias (optional)
    commodity_obj = Commodity.objects.filter(name__iexact=commodity_name).first()
    if not data_qs.exists() and commodity_obj and commodity_obj.alias_marathi:
        data_qs = WebData.objects.filter(
            commodity__iexact=commodity_obj.alias_marathi,
            date__date=query_date   
        )

    # If still no data, return 404 instead of fetching latest
    if not data_qs.exists():
        return Response({'error': f'No data found for commodity: {commodity_name}'}, status=status.HTTP_404_NOT_FOUND)

    results = [
        {
            'commodity': data.commodity,
            'apmc': data.apmc,
            'variety': data.variety,
            'minprice': data.minprice,
            'maxprice': data.maxprice,
            'modalprice': data.modalprice,
            'unit': data.unit,
            'date': data.date.isoformat() if data.date else None,
            'is_latest': (data.date.date() != today)
        }
        for data in data_qs
    ]

    return Response(results)
#@ api to view profile of logged in user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)


#CRUD operations for consumer/farmer added crops
def is_consumer(user):
    return user.job == 'consumer'

def is_farmer(user):
    return user.job == 'farmer'

# List crops
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_crops(request):
    user = request.user
    if is_consumer(user):
        crops = Consumer1.objects.filter(userid=user.id)
        serializer = ConsumerSerializer(crops, many=True)
    elif is_farmer(user):
        crops = Farmer1.objects.filter(id=user.id)
        serializer = FarmerSerializer(crops, many=True)
    else:
        return Response({"error": "User type unknown"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.data)

# Add crop
@api_view(['POST'])
@permission_classes([IsAuthenticated])
# def add_user_crop(request):
#     user = request.user
#     if is_consumer(user):
#         serializer = ConsumerSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(userid=user.id)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#     elif is_farmer(user):
#         serializer = FarmerSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(id=user.id)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#     else:
#         return Response({"error": "User type unknown"}, status=status.HTTP_400_BAD_REQUEST)
    
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
def add_user_crop(request):
    user = request.user

    data = request.data.copy()  # make mutable copy

    # Add user id automatically
    data['userid'] = str(user.id)

    # Set default date if not provided
    if not data.get('date'):
        data['date'] = timezone.now()
    # Set latitude/longitude if not provided (fallback to 0.0)
    if not data.get('latitude'):
        data['latitude'] = 0.0
    if not data.get('longitude'):
        data['longitude'] = 0.0

    if is_consumer(user):
        serializer = ConsumerSerializer(data=data)
    elif is_farmer(user):
        serializer = FarmerSerializer(data=data)
    else:
        return Response({"error": "User type unknown"}, status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        serializer.save(id=str(uuid.uuid4()))
        # serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# Update crop
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_crop(request, crop_id):
    user = request.user
    try:
        if is_consumer(user):
            crop = Consumer1.objects.get(id=crop_id, userid=user.id)
            serializer = ConsumerSerializer(crop, data=request.data, partial=True)
        elif is_farmer(user):
            crop = Farmer1.objects.get(id=crop_id)
            serializer = FarmerSerializer(crop, data=request.data, partial=True)
        else:
            return Response({"error": "User type unknown"}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()  # saves updated fields
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except (Consumer1.DoesNotExist, Farmer1.DoesNotExist):
        return Response({"error": "Crop not found"}, status=status.HTTP_404_NOT_FOUND)

# Delete crop
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_crop(request, crop_id):
    user = request.user
    try:
        if is_consumer(user):
            crop = Consumer1.objects.get(id=crop_id, userid=user.id)
        elif is_farmer(user):
            crop = Farmer1.objects.get(id=crop_id)
        else:
            return Response({"error": "User type unknown"}, status=status.HTTP_400_BAD_REQUEST)

        crop.delete()
        return Response({"message": "Crop deleted successfully"}, status=status.HTTP_200_OK)

    except (Consumer1.DoesNotExist, Farmer1.DoesNotExist):
        return Response({"error": "Crop not found"}, status=status.HTTP_404_NOT_FOUND)