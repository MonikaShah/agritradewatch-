from django.contrib.gis.geos import GEOSGeometry
from .models import Consumer,Page  # or Farmer, UserData if they have geometry
from django.shortcuts import render,get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ConsumerGeoSerializer
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
# from .serializers import UserSerializer, FarmerSerializer, ConsumerSerializer, WebDataSerializer

def landingpage(request):
    return render(request, "syncapp/landingpage.html")

def map_chart(request):
    return render(request, "syncapp/map_chart.html")

def aboutus(request):
    return render(request, 'syncapp/aboutus.html')


# def consumers_map_view(request):
#     return render(request, "syncapp/map.html")

# def consumers_map_merged_view(request):
#     return render(request,"syncapp/map_merged.html")


# def map_user_products(request):
#     return render(request,"syncapp/map_user_products.html")


# def user_products_list(request):
#     qs = Consumer.objects.exclude(geom__isnull=True)
#     user_ids = list(qs.values_list('data__userID', flat=True).distinct())
#     product_names = list(qs.values_list('data__name', flat=True).distinct())
#     return JsonResponse({'userIDs': user_ids, 'products': product_names})

# def map_user_products_list(request):
#     return render(request,"syncapp/map_user_products_list.html")



def page_detail(request, slug):
    """
    Generic view to render a page based on its slug.
    Example slugs: 'about-us', 'disclaimer', 'footer', etc.
    """
    page = get_object_or_404(Page, slug=slug)
    return render(request, 'pages/page_detail.html', {'page': page})
