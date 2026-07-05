import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# -----------------------------------------------------------
# SETUP: Initialize Firebase
# -----------------------------------------------------------
# Replace "serviceAccountKey.json" with the path to your own
# service account key file downloaded from Firebase Console:
# Firebase Console → Project Settings → Service Accounts → Generate new private key
# -----------------------------------------------------------
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# -----------------------------------------------------------
# CUSTOMER DATA: Johnny Kamau
# -----------------------------------------------------------
customer_data = {
    "username":         "jkamau",
    "cust_password":    "5678",           # ⚠️ See security note below
    "cust_first_name":  "johnny",
    "cust_last_name":   "kamau",
    "vehicle_make":     "Toyota",
    "vehicle_model":    "Probox",
    "vehicle_year":     2015,
    "Date_cust_joined": datetime(2025, 1, 15)   # Stored as Firestore Timestamp
}

# -----------------------------------------------------------
# WRITE TO FIRESTORE
# -----------------------------------------------------------
# .document() with no argument = Auto-generated Firestore Document ID
# -----------------------------------------------------------
doc_ref = db.collection("customers").document()
doc_ref.set(customer_data)

print(f"✅ Customer added successfully!")
print(f"   Document ID : {doc_ref.id}")
print(f"   Name        : {customer_data['cust_first_name']} {customer_data['cust_last_name']}")
print(f"   Username    : {customer_data['username']}")
print(f"   Vehicle     : {customer_data['vehicle_year']} {customer_data['vehicle_make']} {customer_data['vehicle_model']}")
print(f"   Joined      : {customer_data['Date_cust_joined'].strftime('%B %d, %Y')}")