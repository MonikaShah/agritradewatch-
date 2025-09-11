from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

from django.core.serializers import serialize
from django.http import JsonResponse
import json, logging
from django.utils.timezone import make_aware
# from .models import Consumer
from .models import Consumer1,User1,Farmer1,WebData,Commodity  # or Farmer, UserData if they have geometry
from .serializers import UserSerializer, FarmerSerializer, ConsumerSerializer, WebDataSerializer
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from django.utils import timezone
from django.contrib.gis.geos import Point
from django.db.models import Count


# //New model 
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
        # Filter for date >= 30 Aug 2025
        filter_date = timezone.make_aware(datetime(2025, 8, 30, 0, 0, 0))
        return Consumer1.objects.filter(date__gte=filter_date)


class WebDataViewSet(viewsets.ModelViewSet):
    queryset = WebData.objects.all()
    serializer_class = WebDataSerializer
    permission_classes = [IsAuthenticated]


logger = logging.getLogger(__name__)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consumers_geojson(request):
    cutoff_date = timezone.make_aware(datetime(2024, 1, 1))    # qs = Consumer1.objects.filter(date__gte=cutoff_date)

    # cutoff_date = timezone.make_aware(datetime(2025,8,30))    # qs = Consumer1.objects.filter(date__gte=cutoff_date)
    qs = Consumer1.objects.filter(date__gte=cutoff_date)

    # Filter consumers
    consumers = Consumer1.objects.filter(date__gte=cutoff_date)
    for c in qs:
        print(f"{c.id} | {c.commodity} | {c.date} | {c.latitude}, {c.longitude}")

    print("🔍 Cutoff date:", cutoff_date)
    print("📊 Total records in DB:", Consumer1.objects.count())
    print("✅ Matching records after filter:", qs.count())
    print(f"🕒 DB date example: {Consumer1.objects.last().date}")
    print(f"🕒 Cutoff date: {cutoff_date}")

    # for obj in qs:
    #     print(f"➡️ Record: {obj.id}, {obj.commodity}, {obj.date}, {obj.latitude}, {obj.longitude}")
    #     print(Consumer1.objects.values('commodity').annotate(total=Count('id')))
    # ✅ Log debug info
    logger.info(f"[consumers_geojson] Filtering consumers with date >= {cutoff_date}")
    logger.info(f"[consumers_geojson] Found {consumers.count()} records")

    features = []
    for c in consumers:
        logger.debug(f"Consumer {c.id}: {c.commodity}, date={c.date}, "
                     f"lat={c.latitude}, lon={c.longitude}")

        if c.latitude is not None and c.longitude is not None:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [c.longitude, c.latitude],
                },
                "properties": {
                    "id": c.id,
                    "name": c.commodity,
                    # "mobile": c.mobile,
                    "date": c.date.isoformat() if c.date else None,
                    "buyingprice": c.buyingprice,   # <-- flatten this
                    "quantitybought": c.quantitybought,   # ✅ add this
                    "unit": c.unit,                       # ✅ optional, but useful
                },
            })

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    logger.info(f"[consumers_geojson] Returning {len(features)} GeoJSON features")
    return JsonResponse(geojson)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agrowon_prices(request):
    # def fetch_agrowon_prices(request):
    product = request.GET.get("product", "").strip()
    if not product:
        return JsonResponse({"error": "No product provided"}, status=400)

    try:
        commodity = Commodity.objects.get(alias_marathi=product)
    except Commodity.DoesNotExist:
        return JsonResponse({"error": f"No commodity found for {product}"}, status=404)

    # 🔹 Example URL (replace with correct Agrowon API/HTML scraping)
    url = f"https://www.agrowon.com/market-daily-price/{product}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return JsonResponse({"error": "Failed to fetch data from Agrowon"}, status=500)

    # 🔹 Parse response (adjust parser as per Agrowon HTML/JSON)
    data = parse_agrowon_response(resp.text)

    # 🔹 Save into WebData
    web_entry, created = WebData.objects.update_or_create(
        source="agrowon",
        commodity=commodity.commodity,
        date=timezone.now().date(),   # today's date
        defaults={
            "minprice": data.get("min"),
            "maxprice": data.get("max"),
            "modalprice": data.get("modal"),
            "unit": data.get("unit", "क्विंटल"),
        },
    )

    return JsonResponse({
        "message": "Data saved",
        "commodity": commodity.commodity,
        "alias_marathi": commodity.alias_marathi,
        "saved": {
            "min": web_entry.minprice,
            "max": web_entry.maxprice,
            "modal": web_entry.modalprice,
            "unit": web_entry.unit,
        }
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def webdata_prices(request):
    commodity_name = request.GET.get('commodity')
    if not commodity_name:
        return JsonResponse({'error': 'Commodity parameter required'}, status=400)

    today = timezone.localdate()

    # Try exact match on WebData.commodity (case-insensitive) for today
    data_qs = WebData.objects.filter(
        commodity__iexact=commodity_name,
        date__date=today
    )

    if not data_qs.exists():
        # If not found, try looking up Commodity table
        commodity_obj = Commodity.objects.filter(name__iexact=commodity_name).first()
        if commodity_obj and commodity_obj.alias_marathi:
            data_qs = WebData.objects.filter(
                commodity__iexact=commodity_obj.alias_marathi,
                date__date=today
            )

    if not data_qs.exists():
        return JsonResponse({'error': 'No data found for today'}, status=404)

    results = []
    for data in data_qs:
        results.append({
            'commodity': data.commodity,
            'apmc': data.apmc,
            'variety': data.variety,
            'minprice': data.minprice,
            'maxprice': data.maxprice,
            'modalprice': data.modalprice,
            'unit': data.unit,
            'date': data.date.isoformat() if data.date else None
        })

    return JsonResponse(results, safe=False)