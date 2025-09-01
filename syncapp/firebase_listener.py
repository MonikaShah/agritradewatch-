import threading
import firebase_admin
from datetime import datetime
from firebase_admin import credentials, firestore
from .models import Consumer, Farmer, UserData
from django.contrib.gis.geos import Point

# Firebase credentials
cred = credentials.Certificate("appConfig.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def convert_firestore_types(obj):
    if isinstance(obj, dict):
        return {k: convert_firestore_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_firestore_types(i) for i in obj]
    elif hasattr(obj, 'ToDatetime'):  # Firestore timestamp objects have ToDatetime()
        return obj.ToDatetime().isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

from django.contrib.gis.geos import Point

def convert_firestore_types(obj):
    if isinstance(obj, dict):
        return {k: convert_firestore_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_firestore_types(i) for i in obj]
    elif hasattr(obj, "ToDatetime"):  # Firestore timestamp object
        return obj.ToDatetime().isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


def handle_change(change, model_class, geom=False):
    data = change.document.to_dict()
    data = convert_firestore_types(data)
    doc_id = change.document.id

    # Safe conversions
    def to_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0

    price = to_float(data.get("pricePerUnit"))
    quantity = to_float(data.get("quantity"))

    # Coordinates
    lat = data.get("location", {}).get("coords", {}).get("latitude")
    lon = data.get("location", {}).get("coords", {}).get("longitude")
    geom_point = Point(lon, lat) if geom and lat is not None and lon is not None else None

    # Product/unit
    product = data.get("name")
    unit = data.get("unit", "kg")

    # Timestamps
    created_at = data.get("createdAt") or data.get("date")
    timestamp = data.get("timestamp")

    defaults = {
        "name": data.get("name"),
        "product": product,
        "price_per_unit": price,
        "quantity": quantity,
        "unit": unit,
        "lat": lat,
        "lng": lon,
        "timestamp": timestamp,
        "created_at": created_at,
    }

    if geom_point:
        defaults["geom"] = geom_point

    try:
        model_class.objects.update_or_create(id=doc_id, defaults=defaults)
    except Exception as e:
        print(f"Failed to insert/update {doc_id}: {e}")

def start_listeners():
    listeners = [
        (db.collection("consumers"), Consumer, True),
        (db.collection("farmers"), Farmer, True),
        (db.collection("users"), UserData, False),
    ]
    for col_ref, model_class, geom in listeners:
        col_ref.on_snapshot(
            lambda snap, changes, read_time, m=model_class, g=geom:
            [handle_change(c, m, g) for c in changes]
        )
    print("Firebase real-time sync running...")
    threading.Event().wait()