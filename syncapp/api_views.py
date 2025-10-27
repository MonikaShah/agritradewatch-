import logging, json, requests, uuid
from datetime import datetime
from bs4 import BeautifulSoup
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt  # ← import here
from django.shortcuts import render, get_object_or_404
from rest_framework import status, generics, viewsets,permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.decorators import method_decorator
from django.db.models import Max, Q

from .models import Consumer1, User1, Farmer1, WebData, Commodity,APMC_Master,APMC_Market_Prices
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    FarmerSerializer,
    ConsumerSerializer,
    WebDataSerializer,
    CommoditySerializer,
    
)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

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
    parser_classes = [MultiPartParser, FormParser]  # 👈 required for images

    def get_queryset(self):
        # Example: only show consumers since 30 Aug 2025
        filter_date = timezone.make_aware(datetime(2025, 8, 30))
        return Consumer1.objects.filter(date__gte=filter_date)


class WebDataViewSet(viewsets.ModelViewSet):
    queryset = WebData.objects.all()
    serializer_class = WebDataSerializer
    permission_classes = [IsAuthenticated]

class CommodityViewSet(viewsets.ModelViewSet):
    queryset = Commodity.objects.all()
    serializer_class = CommoditySerializer
    permission_classes = [permissions.AllowAny]  # 👈 add this line

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
    
    # Optional: preload all user IDs to avoid repeated queries
    user_map = {u.id: u.username for u in User1.objects.all()}


    features = []
    for c in consumers:
        if c.latitude and c.longitude:
            username = user_map.get(c.userid, "unknown")  # lookup username from User1

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [c.longitude, c.latitude],
                },
                "properties": {
                    "id": c.id,
                    "name": c.commodity,
                    "username": username,
                    "commodity": c.commodity,
                    "date": c.date.isoformat() if c.date else None,
                    "buyingprice": c.buyingprice,
                    "quantitybought": c.quantitybought,
                    "unit": c.unit,
                    "image":c.image.url if c.image else None,
                },
            })

    geojson = {
        "message": f"You are authenticated, {request.user.username}",
        "type": "FeatureCollection",
        "features": features,
    }
    return JsonResponse(geojson)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def commodity_count(request):
    commodity = request.GET.get("commodity", "").strip()
    if not commodity:
        return JsonResponse({"error": "Missing commodity parameter"}, status=400)

    count = Consumer1.objects.filter(commodity__iexact=commodity).count()
    return JsonResponse({"commodity": commodity, "count": count})

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
    
# ---------------------------------------------------------------------
# Agmarknet - WEbdata 
# ---------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def webdata_prices(request):
    commodity_name = request.GET.get('commodity')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not commodity_name:
        return JsonResponse({'error': 'Commodity parameter required'}, status=400)

    # 1️⃣ Initialize queryset
    qs = WebData.objects.filter(commodity__iexact=commodity_name)

    # Handle date range
    if start_date:
        qs = qs.filter(date__date__gte=start_date)
    if end_date:
        qs = qs.filter(date__date__lte=end_date)

    # If no data in range, try alias
    if not qs.exists():
        commodity_obj = Commodity.objects.filter(name__iexact=commodity_name).first()
        alias_name = getattr(commodity_obj, "alias_marathi", None)
        if alias_name:
            qs = WebData.objects.filter(commodity__iexact=alias_name)
            if start_date:
                qs = qs.filter(date__date__gte=start_date)
            if end_date:
                qs = qs.filter(date__date__lte=end_date)

    if not qs.exists():
        return JsonResponse({'error': 'No data found in the selected range'}, status=404)


    # 4️⃣ Serialize results
    results = [
        {
            'commodity': data.commodity,
            'apmc_name': data.apmc if data.apmc else None,  # ✅ send name
            'variety': data.variety,
            'minprice': data.minprice,
            'maxprice': data.maxprice,
            'modalprice': data.modalprice,
            'unit': data.unit,
            'date': data.date.isoformat() if data.date else None,
            # 'is_latest': (data.date.date() != today)  # flag if not today's
        }
        for data in qs.order_by('date')
    ]
    
    print("Sending JSON:", results)  # log in server console

    return JsonResponse(results, safe=False)

def consumer_timeline(request, commodity):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    qs = Consumer1.objects.filter(commodity__iexact=commodity)
    if start_date: qs = qs.filter(date__gte=start_date)
    if end_date: qs = qs.filter(date__lte=end_date)
    qs = qs.order_by("date")

    data = [{"date": entry.date.strftime("%Y-%m-%d"),
             "price": entry.buyingprice} for entry in qs]

    return JsonResponse(data, safe=False)

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
    source = request.GET.get('source', 'agmark')
    commodity_name = request.GET.get('commodity')
    if not commodity_name:
        return Response([])

    apmc_name = request.GET.get('apmc')
    date_str = request.GET.get('date')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Determine date filtering
    try:
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            data_qs = WebData.objects.filter(
                commodity__iexact=commodity_name,
                date__date__range=(start_date, end_date)
            )
        else:
            if date_str:
                query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                query_date = timezone.localdate()
            data_qs = WebData.objects.filter(
                commodity__iexact=commodity_name,
                date__date=query_date
            )
    except ValueError:
        return Response([])

    # Try alias if no data
    commodity_obj = Commodity.objects.filter(name__iexact=commodity_name).first()
    if not data_qs.exists() and commodity_obj and commodity_obj.alias_marathi:
        if start_date_str and end_date_str:
            data_qs = WebData.objects.filter(
                commodity__iexact=commodity_obj.alias_marathi,
                date__date__range=(start_date, end_date)
            )
        else:
            data_qs = WebData.objects.filter(
                commodity__iexact=commodity_obj.alias_marathi,
                date__date=query_date
            )

    # Filter by APMC if provided
    if apmc_name:
        data_qs = data_qs.filter(apmc__iexact=apmc_name)

    # Build results
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
            'is_latest': (data.date.date() != timezone.localdate()) if data.date else False
        }
        for data in data_qs.order_by('date')  # order by date for line chart
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


def apmc_list(request):
    apmcs = APMC_Master.objects.all().values('apmc_name', 'district', 'state','latitude', 'longitude')
    return JsonResponse(list(apmcs), safe=False)

def apmc_timeline_ajax(request, apmc_name):
    apmc = get_object_or_404(APMC_Master, apmc_name=apmc_name)
    prices = apmc.market_prices.all().order_by('report_date')
    return render(request, 'syncapp/partials/apmc_timeline.html', {'prices': prices})


# -------------------------------
# 1️⃣  Request password reset email
# -------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

    users = User.objects.filter(email__iexact=email, is_active=True)
    if not users.exists():
        return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)

    for user in users:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"{settings.FRONTEND_URL}/reset/{uid}/{token}/"  # or your app deep link

        subject = render_to_string('registration/password_reset_subject.txt').strip()
        message = render_to_string('registration/password_reset_email_api.html', {
            'user': user,
            'reset_url': reset_url,
        })

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

    return Response({"message": "Password reset email sent successfully"}, status=status.HTTP_200_OK)


# -------------------------------
# 2️⃣  Confirm new password
# -------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    uidb64 = request.data.get('uidb64')
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    if not uidb64 or not token or not new_password:
        return Response(
            {"error": "uidb64, token, and new_password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid user identifier"}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)

def test_api(request):
    return JsonResponse({"ok": True})
