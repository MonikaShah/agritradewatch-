from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout,get_user_model
from django.contrib.gis.geos import GEOSGeometry
from django.views.decorators.http import require_GET
from .models import Consumer1,Page,Commodity,User1,Farmer1,WebData,DtProduce,DamageCrop , FodderListing # or Farmer, UserData if they have geometry
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from .forms import ConsumerForm, FarmerForm,MyCustomPasswordResetForm,DamageForm,SoldForm,BoughtForm,FodderListingForm, FodderOrderForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.utils.translation import gettext
from django.conf import settings
from uuid import uuid4
from itertools import chain
import traceback 
from django.core.cache import cache
from django.db import transaction
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
from django.contrib.auth.views import PasswordResetView
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
# from .serializers import UserSerializer, FarmerSerializer, ConsumerSerializer, WebDataSerializer
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    FarmerSerializer,
    ConsumerSerializer,
    WebDataSerializer,
    
)

from django.utils.translation import gettext as _

from .models import MobileOTP
from syncapp.utils.otp import generate_otp
from syncapp.utils.sms import send_fast2sms_otp

from django.db import DatabaseError
import math
from decimal import Decimal


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse


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
        from collections import defaultdict
        commodity_groups = defaultdict(list)
        with connection.cursor() as cursor:
            # fetch all commodities
            # cursor.execute("SELECT DISTINCT commodity FROM webdata ORDER BY commodity;")
            # all_commodities = [row[0] for row in cursor.fetchall()]
        
            cursor.execute("""
                SELECT DISTINCT c.type, w.commodity
                FROM webdata w
                LEFT JOIN commodity c ON w.commodity = c.name
                ORDER BY c.type, w.commodity;
            """)
            rows = cursor.fetchall()

        # Group commodities by type

            for ctype, commodity in rows:
                ctype = ctype or "Others"  # fallback if type is NULL
                commodity_groups[ctype].append(commodity)


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
            # "commodities": all_commodities,
            # "available_commodities": available_today,
            "commodity_groups": dict(commodity_groups),
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
            FROM apmc_master_new
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

TYPE_CHOICES = {
    'pulse': _('Pulse'),
    'vegetable': _('Vegetable'),
    'fruit': _('Fruit'),
}
# @login_required
@login_required(login_url='/login/')
def map_chart(request):
    print("User:", request.user, "| Authenticated:", request.user.is_authenticated)

    commodities = Commodity.objects.all().order_by("type", "name")
    grouped_commodities = {}

    for c in commodities:
        translated_name = _(c.name)

        print("DB name:", c.name, "| Translated:", translated_name)
        
        has_valid_data = Consumer1.objects.filter(
            Q(commodity__iexact=c.name),  # case-insensitive match
            latitude__isnull=False,
            longitude__isnull=False,
            date__isnull=False
        ).exists()

        # ✅ Translate TYPE safely
        # translated_type = TYPE_CHOICES.get(c.type, c.type)
        translated_type = gettext(c.type.capitalize())

        grouped_commodities.setdefault(translated_type, []).append({
            "name": c.name,
            "label":gettext(c.name), 
            "title": gettext(c.title) if c.title else "",
            "disabled": not has_valid_data
        })
    print("RAW TYPE VALUE:", repr(c.title))

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
            messages.success(request, _("Welcome %(username)s!") % {"username": user.username})            
            return redirect("landingpage")
        else:
            messages.error(request, _("Invalid credentials"))
            return render(request, "syncapp/login.html")
    return render(request, "syncapp/login.html")

@login_required
def web_logout(request):
    logout(request)  # clears session
    messages.info(request, "You have been logged out.")
    return redirect("landingpage")

def profile(request):
    return render(request, "syncapp/profile.html")
def simple_profile(request):
    user = request.user  # logged-in user
    produces = DtProduce.objects.filter(username=user).order_by('-created_at')

    print("🔍 Produces count:", produces.count())
    print("🔍 Produces queryset:", list(produces.values()))

    return render(request, "syncapp/profile.html", {
        "user": user,
        "produces": produces,
    })
def profile_crud(request):
    if request.method == 'POST':
        produce_id = request.POST.get('produce_id')
        action = request.POST.get('action')
        produce = get_object_or_404(DtProduce, id=produce_id, username=request.user)

        if action == 'save':
            form = DtProduceForm(request.POST, request.FILES, instance=produce)
            if form.is_valid():
                form.save()
        elif action == 'delete':
            produce.delete()

    return redirect('simple_profile')

def web_register(request):
    if request.method == "POST":
        try:
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = make_password(request.POST.get("password"))
            name = request.POST.get("name")           # new
            mobile = request.POST.get("mobile_number")       # new
            job = request.POST.get("job")     
            latitude = request.POST.get("latitude")   # new
            longitude = request.POST.get("longitude") # new

            # ----------------------------------------------------------
                # VALIDATION
            # ----------------------------------------------------------

            # Username empty?
            if not username:
                messages.error(request, "Username cannot be empty.")
                return redirect("register")
            # Email validation
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, "Invalid email format.")
                return redirect("register")

            # Mobile: only digits allowed
            if not mobile.isdigit():
                messages.error(request, "Mobile number must contain only digits.")
                return redirect("register")

            # Mobile: correct length (you can set any rule)
            if len(mobile) != 10:
                messages.error(request, "Mobile number must be exactly 10 digits.")
                return redirect("register")

            # Job must be selected
            if not job or job.strip() == "":
                messages.error(request, "Please select a job.")
                return redirect("register")

            # Latitude / Longitude must not be empty
            if not latitude or not longitude or latitude in ["", "null"] or longitude in ["", "null"]:
                messages.error(request, "Location permission required. Allow location and try again.")
                return redirect("register")

            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                messages.error(request, "Invalid location coordinates.")
                return redirect("register")

            if User1.objects.filter(username=username).exists():
                messages.error(request, "Username already taken")
                return redirect("register")
            
            if User1.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
                return redirect("register")
            
            if User1.objects.filter(mobile=mobile).exists():
                messages.error(request, "Mobile number already registered.")
                return redirect("register")
            
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
        except Exception as e:
            logger.error("Registration failed: %s", str(e), exc_info=True)
            messages.error(request, "Something went wrong. Please try again.")
            return redirect("register")
        
    return render(request, "syncapp/register.html")
@login_required
def list_commodities(request):
    try:
        user_id = str(request.user.id)  # Make sure this matches your userid in models
        # Set default tab
        if request.user.job == "consumer":
            default_tab = "bought"
        else:
            default_tab = "sold"
        # Fetch sold and bought commodities
        sold = Farmer1.objects.filter(userid=user_id).order_by('-date')
        bought = Consumer1.objects.filter(userid=user_id).order_by('-date')

        context = {
            'sold': sold,
            'bought': bought,
            "user_role": request.user.job,
            "default_tab": default_tab,
        }
        return render(request, 'syncapp/list_commodities.html', context)
    except Exception as e:
        print("Error in list_commodities view:", str(e))
        return render(request, "syncapp/list_commodities.html", {
            "sold": [],
            "bought": [],
            "user_role": request.user.job,
            "default_tab": "sold",
            "error": str(e)
        })
@login_required
def delete_sold(request, pk):
    item = get_object_or_404(Farmer1, pk=pk, userid=request.user.id)
    if request.method == "POST":
        item.delete()
    return redirect("list_commodities")

@login_required
def add_crop_website(request):
    user = request.user
    view_type = request.GET.get("view", "add")  # ✅ DEFAULT
    form = None
    seller_form = None
    buyer_form = None
    if request.method == "POST":

        # ---------- FARMER ----------
        if user.job == "farmer":
            form = FarmerForm(request.POST, request.FILES)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.userid = str(user.id)
                obj.role = "farmer"
                obj.save()
                return redirect("success_page")

        # ---------- CONSUMER ----------
        elif user.job == "consumer":
            form = ConsumerForm(request.POST, request.FILES)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.userid = str(user.id)
                obj.role = "consumer"
                obj.save()
                return redirect("success_page")

        # ---------- RETAILER ----------
        elif user.job == "retailer":

            seller_form = FarmerForm(request.POST, request.FILES, prefix="seller")
            buyer_form = ConsumerForm(request.POST, request.FILES, prefix="buyer")

            if seller_form.is_valid() and buyer_form.is_valid():

                # SELLER ENTRY
                seller = seller_form.save(commit=False)
                seller.userid = str(user.id)

                seller.role = "retailer"
                seller.latitude = request.POST.get("seller_latitude", 0)
                seller.longitude = request.POST.get("seller_longitude", 0)
                seller.save()

                # BUYER ENTRY
                buyer = buyer_form.save(commit=False)
                buyer.userid = str(user.id)

                buyer.role = "retailer"
                buyer.latitude = request.POST.get("buyer_latitude", 0)
                buyer.longitude = request.POST.get("buyer_longitude", 0)
                buyer.save()

                # return JsonResponse({
                #     "success": True,
                #     "created_entries": ["seller", "buyer"]
                # })
                return redirect("success_page")
            else:
                # Return form errors as JSON
                errors = {
                    "seller_form": seller_form.errors,
                    "buyer_form": buyer_form.errors
                }
                return JsonResponse({"success": False, "errors": errors}, status=400)


    else:
        if user.job == "farmer":
            form = FarmerForm()
        elif user.job == "consumer":
            form = ConsumerForm()
        else:
            seller_form = FarmerForm(prefix="seller")
            buyer_form = ConsumerForm(prefix="buyer")

    return render(
        request,
        "syncapp/add_crop.html",
        {
            "view_type": view_type,
            "form": form if user.job != "retailer" else None,
            "seller_form": seller_form if user.job == "retailer" else None,
            "buyer_form": buyer_form if user.job == "retailer" else None,
            "user": user,
        },
    )

@login_required
def crops_list(request):
    user = request.user
    userid = str(user.id)
    view_type = request.GET.get("view", "all")

    sold_qs = Farmer1.objects.filter(userid=userid)
    bought_qs = Consumer1.objects.filter(userid=userid)
    
    # Convert to list so we can attach attribute
    sold_list = list(sold_qs)
    bought_list = list(bought_qs)

    # Attach type
    for obj in sold_list:
        obj.type = "Sold"

    for obj in bought_list:
        obj.type = "Bought"

    # ROLE BASED LOGIC
    if user.job == "farmer":
        view_type = "sold"
        crops = sold_list

    elif user.job == "consumer":
        view_type = "bought"
        crops = bought_list

    else:  # retailer
        if view_type == "sold":
            crops = sold_list
        elif view_type == "bought":
            crops = bought_list
        else:
            crops = sold_list + bought_list

    # Commodities list
    commodities = sorted({c.commodity for c in crops})
    selected_commodities = request.GET.getlist("commodities") or commodities

    return render(
        request,
        "syncapp/crops_list.html",
        {
            "crops": crops,
            "commodities": commodities,
            "selected_commodities": selected_commodities,
            "view_type": view_type,
        },
    )

# def crops_list(request):
#     user = request.user
#     sort = request.GET.get("sort", "")
#     selected_commodities = request.GET.getlist("commodity[]") or request.GET.getlist("commodity")
#     edit_id = request.GET.get("edit")
#     is_edit = False

#     # ---------- Determine User Role ----------
#     if user.job == "farmer":
#         crops = Farmer1.objects.filter(userid=user.id)
#         form_class = FarmerForm
#         qty_field = "quantitysold"
#         price_field = "sellingprice"
#     else:
#         crops = Consumer1.objects.filter(userid=user.id)
#         form_class = ConsumerForm
#         qty_field = "quantitybought"
#         price_field = "buyingprice"

#     # ---------- Distinct commodities from user's crops ----------
#     commodities = list(crops.values_list("commodity", flat=True).distinct().order_by("commodity"))

#     # If no specific commodity selected, select all
#     if not selected_commodities:
#         selected_commodities = commodities.copy()

#     # ---------- Commodity Filter ----------
#     if selected_commodities and "All" not in selected_commodities:
#         crops = crops.filter(commodity__in=selected_commodities)

#     # ---------- Sorting ----------
#     sort_map = {
#         "date_asc": "date",
#         "date_desc": "-date",
#         "qty_asc": qty_field,
#         "qty_desc": f"-{qty_field}",
#         "price_asc": price_field,
#         "price_desc": f"-{price_field}",
#     }
#     if sort in sort_map:
#         crops = crops.order_by(sort_map[sort])

#     # ---------- Add/Edit Form ----------
#     if edit_id:
#         crop_to_edit = get_object_or_404(crops.model, id=edit_id, userid=user.id)
#         form = form_class(request.POST or None, request.FILES or None, instance=crop_to_edit)
#         is_edit = True
#     else:
#         form = form_class(request.POST or None, request.FILES or None)

#     if request.method == "POST" and form.is_valid():
#         entry = form.save(commit=False)
#         if not edit_id:
#             entry.id = str(uuid4())
#             entry.userid = user.id
#             entry.date = timezone.now()
#             entry.latitude = user.latitude
#             entry.longitude = user.longitude
#         entry.save()
#         return redirect("crops_list")

#     # ---------- Prepare JSON for map ----------
#     crops_json = [
#         {
#             "lat": c.latitude,
#             "lng": c.longitude,
#             "commodity": c.commodity,
#             "price": getattr(c, price_field, None),
#             "quantity": getattr(c, qty_field, None),
#             "unit": c.unit,
#             "date": c.date.strftime("%Y-%m-%d %H:%M") if c.date else "",
#             "image_url": c.image.url if c.image else ""
#         }
#         for c in crops
#     ]

#     # ---------- AJAX Partial Response ----------
#     if request.headers.get("x-requested-with") == "XMLHttpRequest":
#         html = render_to_string(
#             "syncapp/partials/_crop_table.html",
#             {
#                 "crops": crops,
#                 "selected_commodities": selected_commodities,
#                 "user": user,
#                 "sort": sort,
#                 "commodities": commodities,
#             },
#         )
#         return JsonResponse({"html": html})

#     has_crops = crops.exists()

#     return render(
#         request,
#         "syncapp/crops_list.html",
#         {
#             "form": form,
#             "crops": crops,
#             "user": user,
#             "is_edit": is_edit,
#             "has_crops": has_crops,
#             "commodities": commodities,
#             "selected_commodities": selected_commodities,
#             "sort": sort,
#             "crops_json": json.dumps(crops_json),
#         },
#     )


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


class MyPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    form_class = MyCustomPasswordResetForm

    def get_users(self, email):
        """Return all active users matching the email."""
        return User1.objects.filter(email__iexact=email, is_active=True)

def dtDashboard(request):
    
    username = None
    
    if request.user.is_authenticated:
        username = request.user.username  # or request.user.get_full_name()

   
   # Check the user's role.
    user_role = str(
        getattr(request.user, "job", "")
    ).strip().lower()

    can_add_fodder = user_role in ["farmer", "retailer"]

    context = {
        "thela_username": username,
        "can_add_fodder": can_add_fodder,
    }

    return render(request, "syncapp/dt_dashboard.html", context)
    
@csrf_exempt
def update_user_location(request):
    if request.method == "POST" and request.user.is_authenticated:
        data = json.loads(request.body)
        request.user.latitude = data.get("latitude")
        request.user.longitude = data.get("longitude")
        request.user.save()  # Saves inside syncapp_users1 table
        return JsonResponse({"status":"success"})
    return JsonResponse({"status":"error"}, status=400)


@csrf_exempt
def send_otp(request):
    """
    Accepts POST with JSON body:
    {
        "mobile": "9414285894",
        "purpose": "register"  # or "login", "forgot_password"
    }
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    mobile = data.get("mobile")
    purpose = data.get("purpose")

    if not mobile or not purpose:
        return JsonResponse({"error": "Missing mobile or purpose"}, status=400)

    # Generate OTP
    otp = generate_otp()

    # Save to DB with error handling
    try:
        MobileOTP.objects.create(
            mobile=mobile,
            otp=otp,
            purpose=purpose,
            created_at=timezone.now()
        )
    except Exception as e:
        return JsonResponse({"error": f"Database error: {e}"}, status=500)

    # Send SMS with error handling
    try:
        sms_result = send_fast2sms_otp(mobile, otp)
        if sms_result.get("return"):
            return JsonResponse({"status": "sent"})
        else:
            return JsonResponse({"error": "SMS sending failed"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"SMS service error: {e}"}, status=500)

def verify_otp(request):
    mobile = request.POST.get("mobile")
    otp_input = request.POST.get("otp")
    purpose = request.POST.get("purpose")

    try:
        otp_obj = MobileOTP.objects.filter(
            mobile=mobile,
            purpose=purpose
        ).latest("created_at")
    except MobileOTP.DoesNotExist:
        return JsonResponse({"status": "invalid"})

    if otp_obj.is_expired():
        return JsonResponse({"status": "expired"})

    if otp_obj.attempts >= 3:
        return JsonResponse({"status": "blocked"})

    if otp_obj.otp != otp_input:
        otp_obj.attempts += 1
        otp_obj.save()
        return JsonResponse({"status": "wrong"})

    # ✅ OTP verified
    otp_obj.delete()

    if purpose == "login":
        return login_user_by_mobile(request, mobile)

    if purpose == "forgot_password":
        return JsonResponse({"status": "verified", "action": "reset_password"})

    return JsonResponse({"status": "success"})


def login_user_by_mobile(request, mobile):
    try:
        user = User1.objects.get(username=mobile)
    except User1.DoesNotExist:
        return JsonResponse({"status": "no_user"})

    login(request, user)
    return JsonResponse({"status": "logged_in"})
def damage_crop_page(request):
    # Check if user is authenticated and has proper role
    if not request.user.is_authenticated or request.user.job not in ['farmer', 'retailer']:
        messages.error(request, "You are not authorized to report for damage crop.")
        return redirect('login')  # or any page you want to redirect unauthorized users

    if request.method == 'POST':
        form = DamageForm(request.POST)
        if form.is_valid():
            damage = form.save(commit=False)
            damage.user = request.user  # if you track who submitted
            damage.save()
            messages.success(request, "Damage report submitted successfully!")
            return redirect('damage_crop_page')  # or any success page
    else:
        form = DamageForm()
    
    return render(request, 'syncapp/damage_crop.html', {'form': form})

def damage_crop_detail_view(request, pk):
    damage = DamageCrop.objects.get(pk=pk)

    if damage.photo:
        damage_popup = f"<b>{damage.commodity}</b><br><img src='{damage.photo.url}' style='max-width:200px; max-height:150px; display:block; margin-top:5px;'>"
    else:
        damage_popup = f"<b>{damage.commodity}</b><br>No photo uploaded"

    context = {
        "damage": damage,
        "damage_popup": damage_popup,  # ✅ precomputed HTML
    }

    return render(request, "syncapp/view_damage_crop.html", context)

# -----------------------
# SOLD COMMODITY VIEWS
# -----------------------

def edit_sold(request, pk):
    item = get_object_or_404(Farmer1, pk=pk)

    if request.method == 'POST':
        form = SoldForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('list_commodities')
    else:
        # 👇 THIS is what loads old values
        form = SoldForm(instance=item)

    return render(request, 'syncapp/edit_sold.html', {
        'form': form
    })

def delete_sold(request, pk):
    item = get_object_or_404(
        Farmer1,
        pk=pk,
        userid=request.user.id   # 🔒 ownership check
    )

    item.delete()
    messages.success(request, "Sold commodity deleted successfully.")
    return redirect('list_commodities')


# -----------------------
# BOUGHT COMMODITY VIEWS
# -----------------------

def edit_bought(request, pk):
    item = get_object_or_404(Farmer1, pk=pk)
    if request.method == 'POST':
        form = BoughtForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Bought commodity updated successfully.")
            return redirect('list_commodities')
    else:
        form = BoughtForm(instance=item)
    return render(request, 'syncapp/edit_bought.html', {'form': form, 'item': item})

def delete_bought(request, pk):
    item = get_object_or_404(
        Consumer1,
        pk=pk,
        userid=request.user.id   # 🔒 ensure ownership
    )

    item.delete()
    messages.success(request, "Bought commodity deleted successfully.")
    return redirect('list_commodities')


# -----------------------
# VIEW ON MAP
# -----------------------

def view_on_map(request):
    user = request.user
    userid = str(user.id)

    sold = Farmer1.objects.filter(userid=userid)
    bought = Consumer1.objects.filter(userid=userid)

    crops = []

    # Normalize Sold
    for obj in sold:
        crops.append({
            "commodity": obj.commodity,
            "quantity": obj.quantitysold,
            "latitude": obj.latitude,
            "longitude": obj.longitude,
            "type": "Sold",
        })

    # Normalize Bought
    for obj in bought:
        crops.append({
            "commodity": obj.commodity,
            "quantity": obj.quantitybought,
            "latitude": obj.latitude,
            "longitude": obj.longitude,
            "type": "Bought",
        })

    return render(request, "syncapp/map.html", {"crops": crops})

def data_policy(request):
    return render(request, "syncapp/datapolicy.html")
def disclaimer(request):
    return render(request, "syncapp/disclaimer.html")
@login_required
def delete_account(request):
    user = request.user  # current logged-in user

    if request.method == "POST":
        # -----------------------
        # Delete related models
        # -----------------------
        # Farmer and Consumer entries will be deleted automatically via CASCADE
        # But DtProduce and DamageCrop have FK to User1 with on_delete=models.CASCADE
        # So all related data will go automatically

        # Optional: If you want to manually delete media files
        for produce in DtProduce.objects.filter(username=user):
            if produce.photo_or_video:
                produce.photo_or_video.delete(save=False)
            if produce.description_voice:
                produce.description_voice.delete(save=False)

        for damage in DamageCrop.objects.filter(userid=user):
            if damage.photo:
                damage.photo.delete(save=False)

        for farmer in Farmer1.objects.filter(userid=user):
            if farmer.image:
                farmer.image.delete(save=False)

        for consumer in Consumer1.objects.filter(userid=user):
            if consumer.image:
                consumer.image.delete(save=False)

        # -----------------------
        # Finally delete user
        # -----------------------
        user.delete()

        messages.success(request, "Your account and all related data have been deleted permanently.")
        return redirect("landingpage")  # Or login page

    return render(request, "syncapp/delete_account.html")



User = get_user_model()


def _user_job(user):
    return (getattr(user, "job", "") or "").strip().lower()


@login_required
def fodder_listings(request):
    listings = FodderListing.objects.filter(is_active=True)
    return render(
        request,
        "syncapp/fodder/listings.html",
        {"listings": listings},
    )


@login_required
def fodder_add_listing(request):
    # Only farmers and retailers may sell.
    if _user_job(request.user) not in {"farmer", "retailer"}:
        messages.error(
            request,
            "Only registered farmers and retailers can add fodder listings.",
        )
        return redirect("fodder_listings")

    if request.method == "POST":
        form = FodderListingForm(request.POST)

        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller_id = str(request.user.pk)
            listing.save()

            messages.success(request, "Your fodder listing was published.")
            return redirect("fodder_listings")
        else:
            print("FODDER FORM ERRORS:", form.errors)
            print("FODDER NON-FIELD ERRORS:", form.non_field_errors())
    else:
        form = FodderListingForm()

    return render(
        request,
        "syncapp/fodder/add_listing.html",
        {"form": form},
    )


# @login_required
# def fodder_place_order(request, listing_id):
#     listing = get_object_or_404(
#         FodderListing,
#         pk=listing_id,
#         is_active=True,
#     )

#     initial = {
#         "buyer_name": (
#             getattr(request.user, "name", "")
#             or request.user.get_full_name()
#             or request.user.get_username()
#         ),
#         "buyer_email": request.user.email or "",
#         "buyer_phone": getattr(request.user, "mobile", "") or "",
#     }

#     if request.method == "POST":
#         form = FodderOrderForm(
#             request.POST,
#             buyer_user=request.user,
#             listing=listing,
#         )

#         if form.is_valid():
#             # Keep your existing order-saving and email code here.
#             order = form.save(commit=False)
#             order.listing = listing
#             order.buyer_id = str(request.user.pk)

#             order.buyer_name = (
#                 getattr(request.user, "name", "")
#                 or request.user.get_full_name()
#                 or request.user.get_username()
#             )

#             order.buyer_email = (
#                 request.user.email
#                 or form.cleaned_data["buyer_email"]
#             )

#             order.buyer_phone = (
#                 getattr(request.user, "mobile", "")
#                 or form.cleaned_data["buyer_phone"]
#             )

#             order.save()

#             # Find the seller's registered account using its stored ID.
#             seller = User.objects.filter(pk=listing.seller_id).first()

#             if seller and seller.email:
#                 subject = f"MandiGo: New order for {listing.crop_name}"

#                 email_body = f"""
# A new order has been placed for your MandiGo listing.

# ORDER
# Order ID: {order.pk}
# Listing ID: {listing.pk}
# Crop: {listing.crop_name}
# Variety: {listing.variety or "Not specified"}

# BUYER
# Name: {order.buyer_name}
# User ID: {order.buyer_id}
# Email: {order.buyer_email}
# Phone: {order.buyer_phone}

# DELIVERY LOCATION
# State: {order.destination_state}
# District: {order.destination_district}
# Tehsil: {order.destination_tehsil}
# Village: {order.destination_village}
# Latitude: {order.destination_latitude}
# Longitude: {order.destination_longitude}

# ORDER REQUIREMENTS
# Requested tonnes: {order.requested_tonnes or "Not specified"}
# Requested acres: {order.requested_acres or "Not specified"}
# Harvesting required: {"Yes" if order.harvesting_required else "No"}
# Transportation required: {"Yes" if order.transportation_required else "No"}
# Buyer message: {order.buyer_message or "None"}

# Please sign in to MandiGo to follow up with the buyer.
# """

#                 try:
#                     send_mail(
#                         subject,
#                         email_body,
#                         getattr(settings, "DEFAULT_FROM_EMAIL", None),
#                         [seller.email],
#                         fail_silently=False,
#                     )
#                     messages.success(
#                         request,
#                         "Your order has been placed. The seller has been emailed.",
#                     )
#                 except Exception:
#                     # The order is saved even if email delivery fails.
#                     messages.warning(
#                         request,
#                         "Your order was saved, but the seller notification "
#                         "email could not be sent. Please contact the site administrator.",
#                     )
#             else:
#                 messages.warning(
#                     request,
#                     "Your order was saved, but the seller's registered email "
#                     "address could not be found.",
#                 )

#             return redirect("fodder_listings")
#     else:
#         form = FodderOrderForm(
#             initial=initial,
#             buyer_user=request.user,
#             listing=listing,
#         )

#     return render(
#         request,
#         "syncapp/fodder/place_order.html",
#         {
#             "form": form,
#             "listing": listing,
#         },
#     )






def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate straight-line distance between two coordinates.
    Returns distance in kilometres.
    """
    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    # Protect against floating-point rounding errors.
    a = max(0.0, min(1.0, a))

    return 6371.0 * 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )


@login_required
def fodder_place_order(request, listing_id):
    listing = get_object_or_404(
        FodderListing,
        pk=listing_id,
        is_active=True,
    )

    form = FodderOrderForm(
        request.POST or None,
        buyer_user=request.user,
        listing=listing,
    )

    if request.method == "POST" and form.is_valid():

        # -------------------------------------------------
        # 1. Get the requested quantity according to price basis
        # -------------------------------------------------

        if listing.price_basis == "acre":
            quantity = form.cleaned_data.get("requested_acres")

            if quantity is None or quantity <= 0:
                form.add_error(
                    "requested_acres",
                    "Enter a valid number of acres.",
                )

        elif listing.price_basis == "tonne":
            quantity = form.cleaned_data.get("requested_tonnes")

            if quantity is None or quantity <= 0:
                form.add_error(
                    "requested_tonnes",
                    "Enter a valid quantity in tonnes.",
                )

        else:
            quantity = None
            form.add_error(
                None,
                "This listing has an invalid price basis.",
            )

        # Stop if the quantity or price basis is invalid.
        if form.errors:
            return render(
                request,
                "syncapp/fodder/place_order.html",
                {
                    "listing": listing,
                    "form": form,
                },
            )

        quantity = Decimal(str(quantity))
        price = Decimal(str(listing.price or 0))
        harvesting_rate = Decimal(
            str(listing.harvesting_cost or 0)
        )

        # -------------------------------------------------
        # 2. Calculate produce cost
        # -------------------------------------------------

        produce_cost = quantity * price

        # -------------------------------------------------
        # 3. Calculate harvesting cost
        #
        # Add harvesting charges only when:
        # seller has NOT included harvesting, AND
        # buyer has requested harvesting.
        # -------------------------------------------------

        harvesting_required = (
            form.cleaned_data.get("harvesting_required")
        )

        if (
            not listing.harvesting_included
            and harvesting_required is True
        ):
            harvesting_cost = quantity * harvesting_rate
        else:
            harvesting_cost = Decimal("0")

        # -------------------------------------------------
        # 4. Calculate net cost
        # -------------------------------------------------

        net_cost = produce_cost + harvesting_cost

        # -------------------------------------------------
        # 5. Calculate travel cost
        # -------------------------------------------------

        transportation_required = (
            form.cleaned_data.get("transportation_required")
        )

        destination_lat = form.cleaned_data.get(
            "destination_latitude"
        )
        destination_lon = form.cleaned_data.get(
            "destination_longitude"
        )

        seller_lat = listing.latitude
        seller_lon = listing.longitude

        distance_km = None
        travel_cost = Decimal("0")

        if transportation_required is True:

            coordinates_available = all(
                value is not None
                for value in (
                    seller_lat,
                    seller_lon,
                    destination_lat,
                    destination_lon,
                )
            )

            if coordinates_available:
                distance_km = calculate_distance_km(
                    seller_lat,
                    seller_lon,
                    destination_lat,
                    destination_lon,
                )

                transport_rate = Decimal(
                    str(
                        listing.transportation_charge_per_km
                        or 0
                    )
                )

                travel_cost = (
                    Decimal(str(distance_km))
                    * transport_rate
                )

        # -------------------------------------------------
        # 6. Calculate total cost
        # -------------------------------------------------

        total_cost = net_cost + travel_cost

        # -------------------------------------------------
        # 7. Save order
        # -------------------------------------------------

        order = form.save(commit=False)

        order.listing = listing
        order.buyer_id = str(request.user.pk)

        order.buyer_name = (
            getattr(request.user, "name", "")
            or request.user.get_full_name()
            or request.user.get_username()
        )

        order.buyer_email = (
            getattr(request.user, "email", "")
            or form.cleaned_data.get("buyer_email", "")
        )

        order.buyer_phone = (
            getattr(request.user, "mobile", "")
            or form.cleaned_data.get("buyer_phone", "")
        )

        order.save()

        # -------------------------------------------------
        # 8. Notify seller by email
        # -------------------------------------------------

        seller = User.objects.filter(
            pk=listing.seller_id
        ).first()

        if seller and seller.email:

            quantity_unit = (
                "acre"
                if listing.price_basis == "acre"
                else "tonne"
            )

            distance_text = (
                f"{distance_km:.2f} km"
                if distance_km is not None
                else "Unavailable"
            )

            email_subject = (
                f"MandiGo: New order for {listing.crop_name}"
            )

            email_body = f"""
A new fodder order has been placed.

ORDER DETAILS
-------------
Order ID: {order.pk}
Crop: {listing.crop_name}
Variety: {listing.variety or "Not specified"}

QUANTITY
--------
Requested quantity: {quantity} {quantity_unit}
Price: Rs. {price} per {quantity_unit}

BUYER DETAILS
-------------
Name: {order.buyer_name}
Buyer ID: {order.buyer_id}
Email: {order.buyer_email}
Phone: {order.buyer_phone}

HARVESTING
----------
Seller includes harvesting: {
    "Yes" if listing.harvesting_included else "No"
}
Buyer requests harvesting: {
    "Yes" if harvesting_required else "No"
}
Harvesting cost: Rs. {harvesting_cost:.2f}

TRANSPORTATION
--------------
Transportation requested: {
    "Yes" if transportation_required else "No"
}
Estimated straight-line distance: {distance_text}
Transportation rate: Rs. {
    Decimal(str(listing.transportation_charge_per_km or 0))
} per km
Travel cost: Rs. {travel_cost:.2f}

COST SUMMARY
------------
Produce cost: Rs. {produce_cost:.2f}
Harvesting cost: Rs. {harvesting_cost:.2f}
Net cost: Rs. {net_cost:.2f}
Travel cost: Rs. {travel_cost:.2f}
TOTAL COST: Rs. {total_cost:.2f}

DELIVERY LOCATION
-----------------
Latitude: {destination_lat}
Longitude: {destination_lon}

Buyer message:
{form.cleaned_data.get("buyer_message") or "None"}

Note: Travel cost uses straight-line distance, not road distance.
"""

            try:
                send_mail(
                    subject=email_subject,
                    message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[seller.email],
                    fail_silently=False,
                )
            except Exception:
                # The order has already been saved.
                # An email failure should not undo the order.
                import logging

                logging.getLogger(__name__).exception(
                    "Failed to email seller for fodder order %s",
                    order.pk,
                )

        messages.success(
            request,
            (
                f"Order placed successfully. "
                f"Net cost: ₹{net_cost:,.2f}; "
                f"Travel cost: ₹{travel_cost:,.2f}; "
                f"Total cost: ₹{total_cost:,.2f}."
            ),
        )

        return redirect("fodder_listings")

    return render(
        request,
        "syncapp/fodder/place_order.html",
        {
            "listing": listing,
            "form": form,
        },
    )

# GeoServer configuration for the Maharashtra village layer.
MH_VILLAGE_WFS_URL = (
    "https://geonode.communitygis.in/geoserver/ows"
)
MH_VILLAGE_LAYER = "geonode:mh_village"

MH_VILLAGE_FIELDS = [
    "state_ut",
    "state_lgd",
    "district",
    "dist_lgd",
    "sub_dist",
    "subdis_lgd",
    "vill_name",
    "vill_lgd",
]


def _mh_village_cql_value(value):
    """
    Escape a string for use as a CQL string literal.
    """
    return "'" + str(value).replace("'", "''") + "'"


def _mh_village_wfs(params):
    """
    Request GeoJSON from the mh_village WFS layer.
    """
    request_params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetCapabilities",
        "typeNames": MH_VILLAGE_LAYER,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
    }

    request_params.update(params)

    response = requests.get(
        MH_VILLAGE_WFS_URL,
        params=request_params,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()

    if "features" not in data:
        raise ValueError("GeoServer did not return a GeoJSON FeatureCollection.")

    return data


def _mh_village_get_features():
    """
    Fetch and cache village attributes without geometries.

    The cache avoids downloading the complete village list for every
    dropdown selection.
    """
    cache_key = "mandigo_mh_village_attributes_v1"

    cached_features = cache.get(cache_key)

    if cached_features is not None:
        return cached_features

    data = _mh_village_wfs({
        "propertyName": ",".join(MH_VILLAGE_FIELDS),
        "count": 50000,
    })

    features = []

    for feature in data.get("features", []):
        properties = feature.get("properties") or {}

        features.append({
            field: properties.get(field)
            for field in MH_VILLAGE_FIELDS
        })

    cache.set(cache_key, features, 60 * 60)

    return features


@require_GET
def mh_village_dropdown_api(request):
    """
    Return state, district, tehsil or village choices from mh_village.

    Examples:
        ?level=states
        ?level=districts&state=MAHARASHTRA
        ?level=tehsils&state=MAHARASHTRA&district=PARBHANI
        ?level=villages&state=MAHARASHTRA&district=PARBHANI&tehsil=MANWATH
    """
    level = request.GET.get("level", "").strip().lower()

    state = request.GET.get("state", "").strip()
    district = request.GET.get("district", "").strip()
    tehsil = request.GET.get("tehsil", "").strip()

    try:
        features = _mh_village_get_features()

        # Filter progressively by the selected administrative areas.
        if state:
            features = [
                row for row in features
                if str(row.get("state_ut") or "").strip().casefold()
                == state.casefold()
            ]

        if district:
            features = [
                row for row in features
                if str(row.get("district") or "").strip().casefold()
                == district.casefold()
            ]

        if tehsil:
            features = [
                row for row in features
                if str(row.get("sub_dist") or "").strip().casefold()
                == tehsil.casefold()
            ]

        if level == "states":
            field = "state_ut"
            code_field = "state_lgd"

        elif level == "districts":
            if not state:
                return JsonResponse(
                    {"error": "Select a state first."},
                    status=400,
                )

            field = "district"
            code_field = "dist_lgd"

        elif level == "tehsils":
            if not state or not district:
                return JsonResponse(
                    {"error": "Select a state and district first."},
                    status=400,
                )

            field = "sub_dist"
            code_field = "subdis_lgd"

        elif level == "villages":
            if not state or not district or not tehsil:
                return JsonResponse(
                    {"error": "Select a state, district and tehsil first."},
                    status=400,
                )

            field = "vill_name"
            code_field = "vill_lgd"

        else:
            return JsonResponse(
                {"error": "Invalid dropdown level."},
                status=400,
            )

        # Deduplicate choices while retaining their administrative codes.
        unique = {}

        for row in features:
            name = str(row.get(field) or "").strip()
            code = row.get(code_field)

            if not name:
                continue

            key = name.casefold()

            if key not in unique:
                unique[key] = {
                    "name": name,
                    "code": code,
                }

        results = sorted(
            unique.values(),
            key=lambda item: item["name"].casefold(),
        )

        return JsonResponse({"results": results})

    except (requests.RequestException, ValueError) as exc:
        return JsonResponse(
            {
                "error": "Could not retrieve village data from GeoNode.",
                "details": str(exc),
            },
            status=502,
        )


@require_GET
def mh_village_geometry_api(request):
    """
    Return the selected village's GeoJSON geometry.
    """
    village_code = request.GET.get("vill_lgd", "").strip()

    if not village_code.isdigit():
        return JsonResponse(
            {"error": "A valid village LGD code is required."},
            status=400,
        )

    try:
        data = _mh_village_wfs({
            "CQL_FILTER": "vill_lgd=" + village_code,
            "propertyName": ",".join(MH_VILLAGE_FIELDS),
        })

        # The WFS response includes geometry because propertyName
        # does not request its exclusion.
        features = data.get("features", [])

        if not features:
            return JsonResponse(
                {"error": "Village not found."},
                status=404,
            )

        return JsonResponse(features[0])

    except (requests.RequestException, ValueError) as exc:
        return JsonResponse(
            {
                "error": "Could not retrieve village geometry.",
                "details": str(exc),
            },
            status=502,
        )