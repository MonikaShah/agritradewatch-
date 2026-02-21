from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.gis.geos import GEOSGeometry
from .models import Consumer1,Page,Commodity,User1,Farmer1,WebData,DtProduce,DamageCrop # or Farmer, UserData if they have geometry
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from .forms import ConsumerForm, FarmerForm,MyCustomPasswordResetForm,DamageForm,SoldForm,BoughtForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.utils.translation import gettext
from django.conf import settings
from uuid import uuid4
import traceback
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

    if request.method == "POST":

        # ---------- FARMER ----------
        if user.job == "farmer":
            form = FarmerForm(request.POST, request.FILES)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.userid = user.id
                obj.role = "farmer"
                obj.save()
                return redirect("success_page")

        # ---------- CONSUMER ----------
        elif user.job == "consumer":
            form = ConsumerForm(request.POST, request.FILES)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.userid = user.id
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

                return JsonResponse({
                    "success": True,
                    "created_entries": ["seller", "buyer"]
                })
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
    print("🔥 CROPS_LIST VIEW HIT 🔥")

    user = request.user
    userid = str(user.id)
    view_type = request.GET.get("view", "all")

    sold_qs = Farmer1.objects.filter(userid=userid)
    bought_qs = Consumer1.objects.filter(userid=userid)

    # ---- ROLE BASED VISIBILITY ----
    if user.job == "farmer":
        view_type = "sold"
        crops = sold_qs

    elif user.job == "consumer":
        view_type = "bought"
        crops = bought_qs

    else:  # retailer
        if view_type == "sold":
            crops = sold_qs
        elif view_type == "bought":
            crops = bought_qs
        else:  # all
            crops = list(chain(sold_qs, bought_qs))

    # ---- COMMODITIES (SAFE) ----
    if isinstance(crops, list):
        commodities = sorted({c.commodity for c in crops})
    else:
        commodities = list(
            crops.values_list("commodity", flat=True).distinct()
        )

    selected_commodities = request.GET.getlist("commodities") or commodities

    # ---- DEBUG ----
    print("DEBUG user:", user.job)
    print("DEBUG view_type:", view_type)
    print("DEBUG crops count:", len(crops) if isinstance(crops, list) else crops.count())

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

   
    context = {
        "thela_username": username,
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
    # Assuming Farmer1 has latitude and longitude fields
    commodities = Farmer1.objects.all()
    return render(request, 'syncapp/map.html', {'commodities': commodities})

def data_policy(request):
    return render(request, "syncapp/datapolicy.html")
def disclaimer(request):
    return render(request, "syncapp/disclaimer.html")
