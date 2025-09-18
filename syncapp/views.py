from django.contrib.gis.geos import GEOSGeometry
from .models import Consumer1,Page,Commodity,User1 # or Farmer, UserData if they have geometry
from django.shortcuts import render,get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
# from .serializers import ConsumerGeoSerializer
import requests,logging,json
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
# from .serializers import UserSerializer, FarmerSerializer, ConsumerSerializer, WebDataSerializer
logger = logging.getLogger(__name__)
def landingpage(request):
    return render(request, "syncapp/landingpage.html")

def apmc(request):
    """
    Render APMC page (apmcdata.html) or return JSON data
    for AJAX requests (commodity + date filter).
    """
    commodity = request.GET.get("commodity")
    date_str = request.GET.get("date")

    # Case 1: Initial page load → render template
    if not commodity or not date_str:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT commodity FROM webdata ORDER BY commodity;")
            commodities = [row[0] for row in cursor.fetchall()]
        return render(request, "syncapp/apmcdata.html", {"commodities": commodities})

    # Case 2: AJAX data request
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

    sources = ["agrowon", "agmarknet"]
    result = {}

    for source in sources:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT date, modal_price, min_price, max_price, market
                FROM webdata
                WHERE commodity = %s AND source = %s AND date = %s
                ORDER BY market;
            """, [commodity, source, selected_date])
            rows = cursor.fetchall()

        if not rows:
            result[source] = {"status": "Data not available"}
            continue

        prices = []
        for row in rows:
            date, modal_price, min_price, max_price, market = row

            # Convert Rs/quintal → Rs/kg for agmarknet only
            if source == "agmarknet":
                modal_price = round(modal_price / 100, 2) if modal_price else None
                min_price = round(min_price / 100, 2) if min_price else None
                max_price = round(max_price / 100, 2) if max_price else None

            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "market": market,
                "modal_price": modal_price,
                "min_price": min_price,
                "max_price": max_price,
            })

        result[source] = {"status": "ok", "data": prices}

    return JsonResponse({
        "commodity": commodity,
        "date": selected_date.strftime("%Y-%m-%d"),
        "sources": result
    })


def map_chart(request):
    commodities = Commodity.objects.all().order_by("type", "name")
    grouped_commodities = {}

    for c in commodities:
        has_valid_data = Consumer1.objects.filter(
            Q(commodity__iexact=c.name),  # case-insensitive match
            latitude__isnull=False,
            longitude__isnull=False,
            date__isnull=False
        ).exists()

        grouped_commodities.setdefault(c.type, []).append({
            "name": c.name,
            "disabled": not has_valid_data
        })

    return render(request, "syncapp/map_chart.html", {
        "grouped_commodities": grouped_commodities,
    })
    # return render(request, "syncapp/map_chart.html")

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

def web_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            user = User1.objects.get(username=username)
            if check_password(password, user.password):
                request.session["user_id"] = user.id
                messages.success(request, "Login successful!")
                return redirect("/")  # change to dashboard
            else:
                messages.error(request, "Invalid password")
        except User1.DoesNotExist:
            messages.error(request, "User not found")
    return render(request, "syncapp/login.html")


def web_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = make_password(request.POST.get("password"))

        if User1.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
        else:
            User1.objects.create(username=username, email=email, password=password)
            messages.success(request, "Registration successful, please login")
            return redirect("login")
    return render(request, "syncapp/register.html")