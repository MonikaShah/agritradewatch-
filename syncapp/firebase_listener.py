import os,threading
import firebase_admin
from firebase_admin import credentials, firestore,initialize_app
from django.contrib.gis.geos import Point
from .models import Consumer1, Farmer1, User1
from django.utils import timezone

# Initialize Firebase only once
if not firebase_admin._apps:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cred = credentials.Certificate("appConfig.json")
    firebase_admin.initialize_app(cred)
    initialize_app(cred)

db = firestore.client()

def make_aware_if_needed(dt):
    if dt and timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt

def convert_firestore_types(data):
    """
    Optional: convert Firestore Timestamp / other types if needed
    """
    return data


def handle_document(col_name, doc):
    data = doc.to_dict()
    if not data:
        return

    doc_id = doc.id
    data = convert_firestore_types(data)

    if col_name == "consumers":
        lat = data.get("location", {}).get("coords", {}).get("latitude")
        lon = data.get("location", {}).get("coords", {}).get("longitude")
        geom_point = Point(lon, lat) if lat and lon else None

        Consumer1.objects.update_or_create(
            id=doc.id,
            defaults={
                "commodity": data.get("name"),
                "buyingprice": float(data.get("pricePerUnit") or 0),
                "quantitybought": float(data.get("quantity") or 0),
                "unit": data.get("unit", "kg"),
                "latitude": lat,
                "longitude": lon,
                "date": make_aware_if_needed(data.get("date")),
                # "geom": geom_point,
            }
        )

    elif col_name == "farmers":
        # similar logic for Farmer1
        pass

    elif col_name == "users":
        User1.objects.update_or_create(
            id=doc.id,
            defaults={
            "name": data.get("name"),
            "mobile": data.get("mobile"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "job": data.get("job"),
            "username": data.get("username"),
            "createdat": data.get("createdAt"),
        },
        )


def fetch_firestore_and_insert():
    """
    Fetch all collections from Firestore and insert/update Postgres
    """
    collections = db.collections()
    for col in collections:
        for doc in col.stream():
            handle_document(col.id, doc)

    print("✅ Firestore data synced to Postgres")
