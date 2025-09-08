from rest_framework.decorators import api_view
from rest_framework import viewsets
from django.core.serializers import serialize
from django.http import JsonResponse
import json, logging
from django.utils.timezone import make_aware
# from .models import Consumer
from .models import Consumer1,User1,Farmer1,WebData  # or Farmer, UserData if they have geometry
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

class FarmerViewSet(viewsets.ModelViewSet):
    queryset = Farmer1.objects.all()
    serializer_class = FarmerSerializer

class ConsumerViewSet(viewsets.ModelViewSet):
    queryset = Consumer1.objects.all()
    serializer_class = ConsumerSerializer
    def get_queryset(self):
        # Filter for date >= 30 Aug 2025
        filter_date = timezone.make_aware(datetime(2025, 8, 30, 0, 0, 0))
        return Consumer1.objects.filter(date__gte=filter_date)
    

class WebDataViewSet(viewsets.ModelViewSet):
    queryset = WebData.objects.all()
    serializer_class = WebDataSerializer

logger = logging.getLogger(__name__)
@api_view(['GET'])
def consumers_geojson(request):
    cutoff_date = timezone.make_aware(datetime(2025,8,30))    # qs = Consumer1.objects.filter(date__gte=cutoff_date)
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

    for obj in qs:
        print(f"➡️ Record: {obj.id}, {obj.commodity}, {obj.date}, {obj.latitude}, {obj.longitude}")
        print(Consumer1.objects.values('commodity').annotate(total=Count('id')))
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
                    # "sellingprice": c.sellingprice,
                },
            })

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    logger.info(f"[consumers_geojson] Returning {len(features)} GeoJSON features")
    return JsonResponse(geojson)

# def consumer_user_geojson(request, user_id):
#     # Filter by userID
#     consumers = Consumer.objects.filter(data__userID=user_id, geom__isnull=False)

#     # Convert to GeoJSON
#     geojson_str = serialize('geojson', consumers,
#                             geometry_field='geom',
#                             fields=('data', 'name'))
#     geojson_obj = json.loads(geojson_str)

#     # You can merge quantities and pick latest date here if needed
#     # For now, send raw filtered GeoJSON
#     return JsonResponse(geojson_obj)


@api_view(['GET'])
# def avg_consumer_price(request):
#     """
#     Compute average consumer-reported price within a radius
#     ?lat=<lat>&lng=<lng>&radius=<meters>&product=<product_name>
#     """
#     try:
#         lat = float(request.GET.get("lat"))
#         lng = float(request.GET.get("lng"))
#         radius = float(request.GET.get("radius", 500))  # default 1 km
#         product_name = request.GET.get("product")

#         if not product_name:
#             return JsonResponse({"error": "Missing ?product=<name>"}, status=400)

#         user_point = Point(lng, lat, srid=4326)

#         consumers = Consumer.objects.filter(
#             geom__distance_lte=(user_point, radius),
#             data__name=product_name
#         )

#         prices = [
#             float(c.data.get("pricePerUnit", 0))
#             for c in consumers if c.data.get("pricePerUnit") not in (None, "")
#         ]

#         avg_price = sum(prices)/len(prices) if prices else None

#         return JsonResponse({
#             "avg_price": avg_price,
#             "consumer_count": len(prices)
#         })

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
    

@api_view(['GET'])
def agrowon_prices(request):
    product_name = request.GET.get("product")
    if not product_name:
        return JsonResponse({"error": "Missing ?product=<marathi_name>"}, status=400)

    url = "http://agrowon.esakal.com/feapi/msamb"
    today_str = datetime.now().strftime("%d-%m-%Y")

    soap_body = f"""
    <?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                     xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                     xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
      <soap12:Body>
        <get_selected_data xmlns="http://tempuri.org/">
          <from_date>{today_str}</from_date>
          <to_date>{today_str}</to_date>
        </get_selected_data>
      </soap12:Body>
    </soap12:Envelope>
    """

    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
    resp = requests.post(url, data=soap_body.encode("utf-8"), headers=headers, timeout=10)
    resp.encoding = "utf-8"

    root = ET.fromstring(resp.text)
    records = []
    for msamb_data in root.iter("msamb_data"):
        record = {
            tag: (msamb_data.find(tag).text if msamb_data.find(tag) is not None else "")
            for tag in ["r_date", "comm_name", "apmc_name", "variety_name", "unit", "arrivals", "min", "max", "Model"]
        }
        records.append(record)

    df = pd.DataFrame(records)
    df = df[df["comm_name"] == product_name]
    df["farmer_rate"] = None

    return JsonResponse(df.to_dict(orient="records"), safe=False)



# def dashboard(request):
#     return render(request, "syncapp/dashboard.html")


# Crops in Marathi
wanted_crops = ["कांदा", "टोमॅटो", "शेवगा शेंगा", "लिंबू"]

# def fetch_agrowon_data():
#     url = "https://agrowon.esakal.com/feapi/price_by_commodity"
#     response = requests.get(url)
#     print(response.text)

#     if response.status_code != 200:
#         return []

#     root = ET.fromstring(response.content)
#     data = []
#     for item in root.findall("item"):
#         try:
#             crop = item.find("comm_name").text if item.find("comm_name") is not None else ""
#             variety = item.find("variety").text if item.find("variety") is not None else ""
#             modal_price = item.find("modal_price").text if item.find("modal_price") is not None else ""
#             mandi = item.find("market").text if item.find("market") is not None else ""

#             data.append({
#                 "crop": crop,
#                 "variety": variety,
#                 "modal_price": modal_price,
#                 "mandi": mandi,
#             })
#         except Exception as e:
#             print("Parse error:", e)
#     return data

# def agrowon_data(request):
#     try:
#         data = fetch_agrowon_data()
        
#         return JsonResponse({"status": "success", "data": data})
#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)})

