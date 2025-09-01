from django.http import JsonResponse
from django.contrib.gis.geos import GEOSGeometry
from django.core.serializers import serialize
from .models import Consumer  # or Farmer, UserData if they have geometry
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ConsumerGeoSerializer
import json
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance


@api_view(['GET'])
def consumers_geojson(request):
    geojson_str = serialize(
        'geojson',
        Consumer.objects.exclude(geom__isnull=True),  # skip null geometry
        geometry_field='geom',
        fields=('id', 'name', 'data')
    )
    geojson_obj = json.loads(geojson_str)  # convert string to Python dict
    return JsonResponse(geojson_obj)  # now Leaflet gets valid JSON

# def consumers_map_view(request):
#     return render(request, "syncapp/map.html")

# def consumers_map_merged_view(request):
#     return render(request,"syncapp/map_merged.html")


# def map_user_products(request):
#     return render(request,"syncapp/map_user_products.html")

def consumer_user_geojson(request, user_id):
    # Filter by userID
    consumers = Consumer.objects.filter(data__userID=user_id, geom__isnull=False)

    # Convert to GeoJSON
    geojson_str = serialize('geojson', consumers,
                            geometry_field='geom',
                            fields=('data', 'name'))
    geojson_obj = json.loads(geojson_str)

    # You can merge quantities and pick latest date here if needed
    # For now, send raw filtered GeoJSON
    return JsonResponse(geojson_obj)

# def user_products_list(request):
#     qs = Consumer.objects.exclude(geom__isnull=True)
#     user_ids = list(qs.values_list('data__userID', flat=True).distinct())
#     product_names = list(qs.values_list('data__name', flat=True).distinct())
#     return JsonResponse({'userIDs': user_ids, 'products': product_names})

# def map_user_products_list(request):
#     return render(request,"syncapp/map_user_products_list.html")

def map_chart(request):
    return render(request, "syncapp/map_chart.html")

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


@api_view(['GET'])
def avg_consumer_price(request):
    """
    Compute average consumer-reported price within a radius
    ?lat=<lat>&lng=<lng>&radius=<meters>&product=<product_name>
    """
    try:
        lat = float(request.GET.get("lat"))
        lng = float(request.GET.get("lng"))
        radius = float(request.GET.get("radius", 500))  # default 1 km
        product_name = request.GET.get("product")

        if not product_name:
            return JsonResponse({"error": "Missing ?product=<name>"}, status=400)

        user_point = Point(lng, lat, srid=4326)

        consumers = Consumer.objects.filter(
            geom__distance_lte=(user_point, radius),
            data__name=product_name
        )

        prices = [
            float(c.data.get("pricePerUnit", 0))
            for c in consumers if c.data.get("pricePerUnit") not in (None, "")
        ]

        avg_price = sum(prices)/len(prices) if prices else None

        return JsonResponse({
            "avg_price": avg_price,
            "consumer_count": len(prices)
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)