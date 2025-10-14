from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.gis.geos import GEOSGeometry
from .models import Consumer1,Page,Commodity,User1,Farmer1,WebData # or Farmer, UserData if they have geometry
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
import html, uuid
# from .serializers import ConsumerGeoSerializer
import requests,logging,json
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime,timedelta
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.template.loader import render_to_string

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

def apmc(request):
    
    commodity = request.GET.get("commodity")
    date_str = request.GET.get("date")
    today = timezone.localdate()

    apmcs = WebData.objects.values_list('apmc', flat=True).distinct().order_by('apmc')

    # Case 1: Initial page load → render template
    if not commodity or not date_str:
        with connection.cursor() as cursor:
            # fetch all commodities
            cursor.execute("SELECT DISTINCT commodity FROM webdata ORDER BY commodity;")
            all_commodities = [row[0] for row in cursor.fetchall()]

            # latest available date per commodity
            cursor.execute("""
                SELECT commodity, MAX(date)
                FROM webdata
                GROUP BY commodity;
            """)
            rows = cursor.fetchall()

        latest_date_map = {comm: comm_date for comm, comm_date in rows}

        # commodities that have data for today
        available_today = [comm for comm, d in latest_date_map.items() if d == today]

        # fallback logic
        fallback_notice = None
        if not available_today:
            fallback_date = max(latest_date_map.values()) if latest_date_map else today
            fallback_notice = f"No data available for today ({today}), showing latest available data for {fallback_date}."
        else:
            fallback_date = today

        return render(request, "syncapp/apmcdata.html", {
            "commodities": all_commodities,
            "available_commodities": available_today,
            "apmcs": apmcs,
            "today": fallback_date,
            "fallback_notice": fallback_notice,
        })

    # Case 2: AJAX request for specific commodity/date
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
        for date, modal_price, min_price, max_price, market in rows:
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

def ahmedapmc(request):
    apmc_name = request.GET.get("apmc_name")  # optional
    variety = request.GET.get("variety", "Red")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    today = timezone.localdate()

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today - timedelta(days=30)
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today
    except ValueError:
        return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

    # --- Fetch all APMC locations ---
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT apmc_name, latitude, longitude
            FROM apmc_master
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY apmc_name;
        """)
        locations = [{"apmc_name": row[0], "lat": row[1], "lon": row[2]} for row in cursor.fetchall()]

    # --- Fetch prices only if a specific APMC is selected ---
    prices = []
    if apmc_name:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT report_date, variety, modal_price_quintal, min_price_quintal, max_price_quintal
                FROM apmc_market_prices
                WHERE market_name = %s
                  AND variety = %s
                  AND report_date BETWEEN %s AND %s
                ORDER BY report_date ASC;
            """, [apmc_name, variety, start_date, end_date])
            rows = cursor.fetchall()

        for r in rows:
            prices.append({
                "date": r[0].strftime("%Y-%m-%d"),
                "commodity": r[1],
                "modal_price": float(r[2]) if r[2] is not None else 0,
                "min_price": float(r[3]) if r[3] is not None else 0,
                "max_price": float(r[4]) if r[4] is not None else 0,
            })

    return JsonResponse({
        "status": "ok",
        "locations": locations,
        "prices": prices,
    })


def aphmedapmc_market_view(request):
    today = timezone.localdate()

    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT commodity FROM apmc_market_prices ORDER BY commodity;")
        commodities = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT market_name FROM apmc_market_prices ORDER BY market_name;")
        apmcs = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT report_date FROM apmc_market_prices ORDER BY report_date;")
        date_rows = [row[0] for row in cursor.fetchall()]

    # Convert to ISO format for HTML date input
    dates = [d.strftime('%Y-%m-%d') for d in date_rows if d is not None]

    return render(request, 'syncapp/ahmedapmc.html', {
        'commodities': commodities,
        'apmcs': apmcs,
        'dates': dates,
        'today': today,
    })


@login_required
def map_chart(request):
    print("User:", request.user, "| Authenticated:", request.user.is_authenticated)

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
        # "user": request.user, 
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
            login(request, user)  # important, sets session
            messages.success(request, f"Welcome {user.username}!")
            
            return redirect("landingpage")
        else:
            messages.error(request, "Invalid credentials")
    return render(request, "syncapp/login.html")

@login_required
def web_logout(request):
    logout(request)  # clears session
    messages.info(request, "You have been logged out.")
    return redirect("landingpage")

def profile(request):
    return render(request, "syncapp/profile.html")

def web_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = make_password(request.POST.get("password"))
        name = request.POST.get("name")           # new
        mobile = request.POST.get("mobile_number")       # new
        job = request.POST.get("job")     
        latitude = request.POST.get("latitude")   # new
        longitude = request.POST.get("longitude") # new


        if User1.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
        else:
            User1.objects.create(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                password=password,
                name=name,
                mobile=mobile,
                job=job,
                latitude=latitude,
                longitude=longitude
            )
            messages.success(request, "Registration successful, please login")
            return redirect("login")
    return render(request, "syncapp/register.html")

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from uuid import uuid4
from django.utils import timezone
from .models import Farmer1, Consumer1, Commodity
from .forms import FarmerForm, ConsumerForm
import json

@login_required
def crops_list(request):
    user = request.user
    sort = request.GET.get("sort", "")
    selected_commodities = request.GET.getlist("commodity[]") or request.GET.getlist("commodity")
    edit_id = request.GET.get("edit")
    is_edit = False

    # ---------- Determine User Role ----------
    if user.job == "farmer":
        crops = Farmer1.objects.filter(userid=user.id)
        form_class = FarmerForm
        qty_field = "quantitysold"
        price_field = "sellingprice"
    else:
        crops = Consumer1.objects.filter(userid=user.id)
        form_class = ConsumerForm
        qty_field = "quantitybought"
        price_field = "buyingprice"

    # ---------- Distinct commodities from user's crops ----------
    commodities = list(crops.values_list("commodity", flat=True).distinct().order_by("commodity"))

    # If no specific commodity selected, select all
    if not selected_commodities:
        selected_commodities = commodities.copy()

    # ---------- Commodity Filter ----------
    if selected_commodities and "All" not in selected_commodities:
        crops = crops.filter(commodity__in=selected_commodities)

    # ---------- Sorting ----------
    sort_map = {
        "date_asc": "date",
        "date_desc": "-date",
        "qty_asc": qty_field,
        "qty_desc": f"-{qty_field}",
        "price_asc": price_field,
        "price_desc": f"-{price_field}",
    }
    if sort in sort_map:
        crops = crops.order_by(sort_map[sort])

    # ---------- Add/Edit Form ----------
    if edit_id:
        crop_to_edit = get_object_or_404(crops.model, id=edit_id, userid=user.id)
        form = form_class(request.POST or None, request.FILES or None, instance=crop_to_edit)
        is_edit = True
    else:
        form = form_class(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        if not edit_id:
            entry.id = str(uuid4())
            entry.userid = user.id
            entry.date = timezone.now()
            entry.latitude = user.latitude
            entry.longitude = user.longitude
        entry.save()
        return redirect("crops_list")

    # ---------- Prepare JSON for map ----------
    crops_json = [
        {
            "lat": c.latitude,
            "lng": c.longitude,
            "commodity": c.commodity,
            "price": getattr(c, price_field, None),
            "quantity": getattr(c, qty_field, None),
            "unit": c.unit,
            "date": c.date.strftime("%Y-%m-%d %H:%M") if c.date else "",
            "image_url": c.image.url if c.image else ""
        }
        for c in crops
    ]

    # ---------- AJAX Partial Response ----------
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "syncapp/partials/_crop_table.html",
            {
                "crops": crops,
                "selected_commodities": selected_commodities,
                "user": user,
                "sort": sort,
                "commodities": commodities,
            },
        )
        return JsonResponse({"html": html})

    has_crops = crops.exists()

    return render(
        request,
        "syncapp/crops_list.html",
        {
            "form": form,
            "crops": crops,
            "user": user,
            "is_edit": is_edit,
            "has_crops": has_crops,
            "commodities": commodities,
            "selected_commodities": selected_commodities,
            "sort": sort,
            "crops_json": json.dumps(crops_json),
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