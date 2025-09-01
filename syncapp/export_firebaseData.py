import firebase_admin
from firebase_admin import credentials, firestore
import json

cred = credentials.Certificate("appConfig.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

all_data = {}

collections = db.collections()
for col in collections:
    all_data[col.id] = {}
    for doc in col.stream():
        all_data[col.id][doc.id] = doc.to_dict()

# Save to JSON file
with open("firestore_export.json", "w") as f:
    json.dump(all_data, f, indent=4, default=str)

print("✅ Firestore data exported to firestore_export.json")
