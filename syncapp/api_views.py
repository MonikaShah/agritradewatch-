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
