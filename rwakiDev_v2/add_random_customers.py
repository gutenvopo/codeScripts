import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# FIREBASE SETUP
# ============================================================
cred = credentials.Certificate(r"C:\Users\kirwa\Documents\coding\codeScripts\rwakiDev_v3\serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ============================================================
# RANDOM DATA POOLS  (Kenyan-flavoured)
# ============================================================
FIRST_NAMES = [
    "James", "Grace", "Brian", "Faith", "Kevin",
    "Mercy", "David", "Lydia", "Peter", "Cynthia",
    "Samuel", "Esther", "Daniel", "Pauline", "George",
    "Irene", "Michael", "Violet", "Patrick", "Caroline",
]

LAST_NAMES = [
    "Kamau", "Otieno", "Wanjiku", "Muthoni", "Odhiambo",
    "Kimani", "Achieng", "Njoroge", "Waweru", "Omondi",
    "Kariuki", "Adhiambo", "Gitau", "Njenga", "Onyango",
    "Mwangi", "Auma", "Ndungu", "Wairimu", "Owino",
]

VEHICLE_MAKES = ["Toyota", "Nissan", "Mazda", "Honda", "Mitsubishi", "Subaru", "Hyundai", "Ford", "Volkswagen", "Isuzu"]

VEHICLE_MODELS = {
    "Toyota":      ["Probox", "Hilux", "Corolla", "Land Cruiser", "Prado", "Fortuner", "Vitz"],
    "Nissan":      ["Note", "Tiida", "X-Trail", "Navara", "Patrol", "March"],
    "Mazda":       ["Demio", "CX-5", "Atenza", "BT-50", "Axela"],
    "Honda":       ["Fit", "CR-V", "Civic", "Accord", "HR-V"],
    "Mitsubishi":  ["Outlander", "Pajero", "Eclipse Cross", "L200", "Colt"],
    "Subaru":      ["Forester", "Outback", "Legacy", "Impreza", "XV"],
    "Hyundai":     ["Elantra", "Tucson", "Santa Fe", "i10", "Creta"],
    "Ford":        ["Ranger", "Everest", "EcoSport", "Explorer", "Fusion"],
    "Volkswagen":  ["Golf", "Polo", "Tiguan", "Passat", "Amarok"],
    "Isuzu":       ["D-Max", "MU-X", "NPR", "Forward", "FRR"],
}

KENYAN_PREFIXES = ["+2547", "+2541"]

def random_phone():
    prefix = random.choice(KENYAN_PREFIXES)
    number = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + number

def random_date_joined():
    # Random date between Jan 2022 and today
    start = datetime(2022, 1, 1)
    end   = datetime.now()
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def random_username(first, last):
    styles = [
        f"{first[0].lower()}{last.lower()}",
        f"{first.lower()}{last[0].lower()}",
        f"{first.lower()}.{last.lower()}",
        f"{first.lower()}{random.randint(10,99)}",
        f"{last.lower()}{first[0].lower()}",
    ]
    return random.choice(styles)

# ============================================================
# GENERATE & UPLOAD 10 UNIQUE CUSTOMERS
# ============================================================
print("\n🚗  Car Mech Pro — Adding 10 Random Customers\n" + "─"*45)

used_names = set()
added = 0
attempts = 0

while added < 10 and attempts < 100:
    attempts += 1

    first = random.choice(FIRST_NAMES)
    last  = random.choice(LAST_NAMES)

    # Ensure unique name combinations
    if (first, last) in used_names:
        continue
    used_names.add((first, last))

    make    = random.choice(VEHICLE_MAKES)
    model   = random.choice(VEHICLE_MODELS[make])
    year    = random.randint(2005, 2024)
    phone   = random_phone()
    joined  = random_date_joined()
    uname   = random_username(first, last)
    email   = f"{uname}@email.com"

    customer = {
        "username":         email,
        "cust_first_name":  first,
        "cust_last_name":   last,
        "cellphone":        phone,
        "vehicle_make":     make,
        "vehicle_model":    model,
        "vehicle_year":     year,
        "Date_cust_joined": joined,
    }

    try:
        doc_ref = db.collection("customers").document()
        doc_ref.set(customer)
        added += 1
        print(f"  ✅ [{added:02d}] {first} {last:<12} | {make} {model} {year} | {email}")
    except Exception as e:
        print(f"  ❌ Error adding {first} {last}: {e}")

print("─"*45)
print(f"\n✔  Done! {added} customers added to Firebase.\n")
