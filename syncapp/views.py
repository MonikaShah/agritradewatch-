from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.gis.geos import GEOSGeometry
from .models import Consumer1,Page,Commodity,User1,Farmer1 # or Farmer, UserData if they have geometry
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from .forms import ConsumerForm, FarmerForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings
from uuid import uuid4
from django.utils import timezone
import html
# from .serializers import ConsumerGeoSerializer
import requests,logging,json
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
# from .serializers import UserSerializer, FarmerSerializer, ConsumerSerializer, WebDataSerializer
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    FarmerSerializer,
    ConsumerSerializer,
    WebDataSerializer,
    
)
logger = logging.getLogger(__name__)
def landingpage(request):
    return render(request, "syncapp/landingpage.html")

@login_required
def apmc(request):
    """
    Render APMC page (apmcdata.html) or return JSON data
    for AJAX requests (commodity + date filter).
    """

     # Extra safety: double-check user is authenticated
    if not request.user.is_authenticated:
        return redirect(settings.LOGIN_URL)

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
    page.content = html.unescape(page.content)  # decode &lt;p&gt; → <p>

    return render(request, 'pages/page_detail.html', {'page': page})


def web_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)  # important
            messages.success(request, f"Welcome {user.username}!")
            return redirect("landingpage")
        else:
            messages.error(request, "Invalid credentials")
    return render(request, "syncapp/login.html")

@login_required
def web_logout(request):
    logout(request)  # clears session
    messages.info(request, "You have been logged out.")
    return redirect("login")

def profile(request):
    return render(request, "syncapp/profile.html")

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


@login_required
# def crops_list(request):
#     user = request.user
#     form = None
#     crops = None
#     print("job is ",user.job)
#     if user.job == "farmer":
#         if request.method == "POST":
#             form = FarmerForm(request.POST)
#             if form.is_valid():
#                 farmer_entry = form.save(commit=False)
#                 farmer_entry.id = str(uuid4()) 
#                 farmer_entry.latitude = user.latitude
#                 farmer_entry.longitude = user.longitude
#                 farmer_entry.save()
#                 return redirect("crops_list")
#         else:
#             form = FarmerForm()
#         crops = Farmer1.objects.filter(id=user.id)

#     elif user.job == "consumer":
#         if request.method == "POST":
#             form = ConsumerForm(request.POST)
#             if form.is_valid():
#                 consumer_entry = form.save(commit=False)
#                 consumer_entry.id = str(uuid4())  # generate new UUID
#                 consumer_entry.userid = user.id
#                 consumer_entry.latitude = user.latitude
#                 consumer_entry.longitude = user.longitude
#                 consumer_entry.save()
#                 return redirect("crops_list")
#         else:
#             form = ConsumerForm()
#         crops = Consumer1.objects.filter(userid=user.id)

#     return render(request, "syncapp/crops_list.html", {"form": form, "crops": crops, "user": user})
def crops_list(request):
    user = request.user
    edit_id = request.GET.get("edit")  # check if editing an existing crop
    print("Edit ID from GET:", edit_id)
    form = None
    crops = None
    is_edit = False  # flag for template
    print("job is", user.job)

    if user.job == "farmer":
        crops = Farmer1.objects.filter(id=user.id)
        if edit_id:
            crop_to_edit = get_object_or_404(Farmer1, id=edit_id)
            form = FarmerForm(request.POST or None, instance=crop_to_edit)
            is_edit = True
        else:
            form = FarmerForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            entry = form.save(commit=False)
            if not edit_id:
                entry.id = str(uuid4())  # generate UUID only for new crop
            entry.latitude = user.latitude
            entry.longitude = user.longitude
            if not edit_id:
                entry.date = timezone.now()  # auto-set datetime for new crop
            entry.save()
            return redirect("crops_list")

    elif user.job == "consumer":
        crops = Consumer1.objects.filter(userid=user.id)
        if edit_id:
            crop_to_edit = get_object_or_404(Consumer1, id=edit_id, userid=user.id)
            form = ConsumerForm(request.POST or None, instance=crop_to_edit)
            is_edit = True
        else:
            form = ConsumerForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            entry = form.save(commit=False)
            if not edit_id:
                entry.id = str(uuid4())  # generate new UUID for new crop
                entry.userid = user.id
                entry.date = timezone.now()
            entry.latitude = user.latitude
            entry.longitude = user.longitude
            entry.save()
            return redirect("crops_list")

    return render(
        request,
        "syncapp/crops_list.html",
        {
            "form": form,
            "crops": crops,
            "user": user,
            "is_edit": is_edit,  # pass flag to template
        },
    )
@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def update_crop(request, crop_id):
    user = request.user

    if user.job == "consumer":
        crop = get_object_or_404(Consumer1, id=crop_id, userid=user.id)
        serializer = ConsumerSerializer(crop, data=request.data, partial=True)
        
    else:
        crop = get_object_or_404(Farmer1, id=crop_id)
        serializer = FarmerSerializer(crop, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)

    return Response(serializer.errors, status=400)


@login_required
def delete_crop(request, crop_id):
    user = request.user

    try:
        if user.job == "consumer":
            crop = get_object_or_404(Consumer1, id=crop_id, userid=user.id)
        else:  # farmer
            crop = get_object_or_404(Farmer1, id=crop_id)

        crop.delete()
        messages.success(request, "Crop deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting crop: {str(e)}")

    return redirect("crops_list")
