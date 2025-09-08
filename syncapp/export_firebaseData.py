# import firebase_admin
# from firebase_admin import credentials, firestore
# import json

# cred = credentials.Certificate("appConfig.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# all_data = {}

# collections = db.collections()
# for col in collections:
#     all_data[col.id] = {}
#     for doc in col.stream():
#         all_data[col.id][doc.id] = doc.to_dict()

# # Save to JSON file
# with open("firestore_export.json", "w") as f:
#     json.dump(all_data, f, indent=4, default=str)

# print("✅ Firestore data exported to firestore_export.json")


import firebase_admin
from firebase_admin import credentials, firestore
from django.contrib.gis.geos import Point
from .models import Consumer1, Farmer1, User1

def initialize_firestore():
    """Initialize Firebase app and return Firestore client."""
    cred = credentials.Certificate("appConfig.json")
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(cred)
    return firestore.client()

def save_to_db(doc, model_class, geom=False):
    """Insert or update Firestore document into Postgres."""
    data = doc.to_dict()
    if not data:
        return

    doc_id = doc.id
    lat = data.get("location", {}).get("coords", {}).get("latitude")
    lon = data.get("location", {}).get("coords", {}).get("longitude")
    geom_point = Point(lon, lat) if geom and lat and lon else None

    defaults = {
        "name": data.get("name"),
        "commodity": data.get("name"),
        "buyingprice": float(data.get("pricePerUnit") or 0),
        "quantitybought": float(data.get("quantity") or 0),
        "unit": data.get("unit", "kg"),
        "latitude": lat,
        "longitude": lon,
        "date": data.get("createdAt") or data.get("timestamp"),
    }
    if geom_point:
        defaults["geom"] = geom_point

    try:
        model_class.objects.update_or_create(firebase_id=doc_id, defaults=defaults)
    except Exception as e:
        print(f"❌ Failed to insert/update {doc_id}: {e}")

def fetch_and_insert_all():
    """Fetch all Firestore data and insert into Postgres."""
    db = initialize_firestore()

    # Only collections you want to sync
    mapping = {
        "consumers": (Consumer1, True),
        "farmers": (Farmer1, True),
        "users": (User1, False),
    }

    for col_name, (model_class, geom) in mapping.items():
        collection_ref = db.collection(col_name)
        for doc in collection_ref.stream():
            save_to_db(doc, model_class, geom)

    print("🔥 Firestore data synced into Postgres!")
