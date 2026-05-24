"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PRODUCTION-GRADE MONGODB SEED SCRIPT                      ║
║              AI-Powered Event Marketplace | Event App Platform               ║
║                                                                              ║
║  SAFETY: Every document has _is_test_data=True and _seed_tag="SEED_TEST_v1" ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import uuid
import hashlib
import random
import json
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any
from passlib.context import CryptContext

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

SEED_TAG = "SEED_TEST_v1"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "eventapp"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
PASSWORD_HASH = pwd_context.hash("Test@1234")

INDIAN_FIRST_NAMES = [
    "Priya","Rahul","Anita","Vikram","Sneha","Arjun","Kavita","Rohit",
    "Pooja","Amit","Divya","Suresh","Meera","Kiran","Ravi","Neha",
    "Ajay","Sunita","Deepak","Rekha","Sanjay","Geeta","Manoj","Sita",
    "Anil","Usha","Vijay","Lata","Ramesh","Savita","Rakesh","Asha",
    "Dinesh","Nisha","Sunil","Poonam","Mukesh","Radha","Arun","Seema",
    "Vinod","Manju","Rajesh","Pushpa","Naresh","Kamla","Mahesh","Shanti",
    "Yogesh","Pinky","Girish","Renu","Hitesh","Komal","Paresh","Hema"
]

INDIAN_LAST_NAMES = [
    "Sharma","Verma","Singh","Patel","Gupta","Mehta","Joshi","Kumar",
    "Agarwal","Tiwari","Nair","Pillai","Reddy","Rao","Shankar","Malhotra",
    "Dubey","Yadav","Mishra","Pandey","Srivastava","Chauhan","Bhatt","Shah",
    "Jain","Saxena","Kapoor","Khanna","Bose","Chatterjee","Das","Ghosh",
    "Iyer","Menon","Krishnan","Murthy","Hegde","Shetty","Naik","Gowda"
]

INDIAN_CITIES = [
    "Mumbai","Delhi","Bangalore","Chennai","Pune","Hyderabad","Kolkata","Jaipur",
    "Ahmedabad","Surat","Lucknow","Kanpur","Nagpur","Indore","Bhopal","Patna"
]

INDIAN_STATES = {
    "Mumbai": "Maharashtra", "Pune": "Maharashtra", "Nagpur": "Maharashtra",
    "Delhi": "Delhi", "Jaipur": "Rajasthan",
    "Bangalore": "Karnataka", "Hyderabad": "Telangana",
    "Chennai": "Tamil Nadu", "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat", "Surat": "Gujarat",
    "Lucknow": "Uttar Pradesh", "Kanpur": "Uttar Pradesh",
    "Indore": "Madhya Pradesh", "Bhopal": "Madhya Pradesh",
    "Patna": "Bihar"
}

VENDOR_CATEGORY_CONFIGS = [
    {"name":"Photography",  "type":"photography",  "commission_bps":1000},
    {"name":"Catering",     "type":"catering",     "commission_bps":1200},
    {"name":"Decoration",   "type":"decoration",   "commission_bps":1500},
    {"name":"Venue",        "type":"venue",        "commission_bps":800},
    {"name":"Music & DJ",   "type":"music",        "commission_bps":1000},
    {"name":"Makeup",       "type":"makeup",       "commission_bps":1200},
    {"name":"Mehendi",      "type":"mehendi",      "commission_bps":1000},
    {"name":"Transport",    "type":"transport",    "commission_bps":800},
]

PRICE_RANGES = {
    "photography":  (1500000,  15000000),
    "catering":     (5000000,  50000000),
    "decoration":   (2000000,  50000000),
    "venue":        (5000000, 100000000),
    "music":        (1500000,  10000000),
    "makeup":       (500000,    5000000),
    "mehendi":      (300000,    3000000),
    "transport":    (500000,    5000000),
}

EVENT_TYPES = ["wedding","corporate","birthday","anniversary","graduation","engagement"]

BOOKING_STATUSES = ["payment_received","vendor_accepted","confirmed","completed","cancelled","disputed"]

PAYMENT_METHODS = ["card","upi","netbanking","wallet"]

REFUND_REASONS = [
    "Vendor unavailable on event date",
    "Customer changed event plans",
    "Quality not as expected",
    "Double booking by vendor",
    "Customer requested cancellation",
    "Vendor did not show up",
    "Service not delivered as promised",
]

DISPUTE_REASONS = [
    "Vendor did not deliver agreed services",
    "Quality was far below expectations",
    "Vendor arrived 3 hours late",
    "Wrong items delivered",
    "Overcharged compared to agreed amount",
]

GROCERY_DATA = {
    "vegetables": [
        ("Aloo","आलू",200,"kg",50,True),
        ("Pyaaz","प्याज",300,"kg",40,True),
        ("Tamatar","टमाटर",400,"kg",35,True),
        ("Palak","पालक",250,"piece",30,True),
        ("Bhindi","भिंडी",500,"kg",25,True),
        ("Gobhi","गोभी",350,"piece",20,True),
        ("Matar","मटर",600,"kg",30,True),
        ("Gajar","गाजर",300,"kg",40,True),
        ("Shimla Mirchi","शिमला मिर्च",800,"kg",20,True),
        ("Baingan","बैंगन",250,"kg",25,True),
        ("Lauki","लौकी",200,"piece",30,True),
        ("Kaddu","कद्दू",180,"kg",15,True),
        ("Arbi","अरबी",400,"kg",20,True),
        ("Methi","मेथी",200,"piece",25,True),
        ("Karela","करेला",450,"kg",20,True),
    ],
    "fruits": [
        ("Kela","केला",200,"dozen",50,True),
        ("Seb","सेब",800,"kg",40,True),
        ("Santara","संतरा",600,"kg",35,True),
        ("Angoor","अंगूर",1200,"kg",25,True),
        ("Aam","आम",600,"kg",20,True),
        ("Papita","पपीता",300,"piece",30,True),
        ("Tarbuj","तरबूज",250,"kg",15,True),
        ("Anaar","अनार",1500,"piece",20,True),
        ("Nashpati","नाशपाती",700,"kg",25,True),
        ("Chiku","चीकू",500,"kg",30,True),
        ("Guava","अमरूद",400,"kg",35,True),
        ("Litchi","लीची",1000,"kg",15,True),
    ],
    "dairy": [
        ("Amul Doodh","अमूल दूध",6800,"litre",100,True),
        ("Dahi","दही",4500,"kg",60,True),
        ("Paneer","पनीर",35000,"kg",30,True),
        ("Amul Ghee","अमूल घी",70000,"litre",25,True),
        ("Makhan","मक्खन",25000,"pack",40,True),
        ("Amul Cream","अमूल क्रीम",3500,"pack",50,True),
        ("Chaas","छाछ",2000,"litre",40,True),
        ("Lassi","लस्सी",2500,"pack",45,True),
        ("Condensed Milk","कंडेंस्ड मिल्क",4500,"pack",30,True),
        ("Cheese Slice","चीज़ स्लाइस",12000,"pack",25,True),
    ],
    "grains": [
        ("Basmati Rice","बासमती चावल",18000,"kg",50,True),
        ("Gehun Atta","गेहूं आटा",5500,"kg",60,True),
        ("Besan","बेसन",8000,"kg",40,True),
        ("Moong Dal","मूंग दाल",12000,"kg",35,True),
        ("Masoor Dal","मसूर दाल",10000,"kg",45,True),
        ("Chana Dal","चना दाल",9000,"kg",40,True),
        ("Toor Dal","तुअर दाल",13000,"kg",35,True),
        ("Urad Dal","उड़द दाल",14000,"kg",30,True),
        ("Maida","मैदा",4500,"kg",50,True),
        ("Sooji","सूजी",5000,"kg",45,True),
        ("Poha","पोहा",6000,"kg",40,True),
        ("Sabudana","साबूदाना",9000,"kg",25,True),
        ("Rajma","राजमा",11000,"kg",30,True),
        ("Kabuli Chana","काबुली चना",10000,"kg",35,True),
        ("Bajra","बाजरा",4000,"kg",25,True),
    ],
    "spices": [
        ("Haldi","हल्दी",2000,"gram",60,True),
        ("Jeera","जीरा",4000,"gram",55,True),
        ("Dhania Powder","धनिया पाउडर",2500,"gram",50,True),
        ("Lal Mirchi","लाल मिर्च",3500,"gram",45,True),
        ("Garam Masala","गरम मसाला",5000,"pack",40,True),
        ("Hing","हींग",8000,"gram",30,True),
        ("Kali Mirch","काली मिर्च",12000,"gram",35,True),
        ("Elaichi","इलायची",35000,"gram",20,True),
        ("Dalchini","दालचीनी",8000,"gram",30,True),
        ("Laung","लौंग",40000,"gram",25,True),
        ("Ajwain","अजवाइन",3000,"gram",40,True),
        ("Methi Dana","मेथी दाना",2500,"gram",35,True),
    ],
    "beverages": [
        ("Tata Chai","टाटा चाय",35000,"gram",40,True),
        ("Bru Coffee","ब्रू कॉफी",45000,"gram",35,True),
        ("Roohafza","रूहाफ़ज़ा",18000,"pack",30,True),
        ("Rasna","रसना",5000,"pack",50,True),
        ("Tropicana Juice","ट्रॉपिकाना जूस",12000,"litre",40,True),
        ("Real Juice","रियल जूस",10000,"litre",45,True),
        ("Complan","कॉम्प्लान",35000,"gram",25,True),
        ("Horlicks","हॉर्लिक्स",32000,"gram",30,True),
    ],
    "snacks": [
        ("Haldiram Namkeen","हल्दीराम नमकीन",8000,"pack",60,True),
        ("Parle G","पारले जी",500,"pack",100,True),
        ("Monaco Biscuit","मोनाको बिस्किट",2000,"pack",80,True),
        ("Kurkure","कुरकुरे",2000,"pack",70,True),
        ("Lays Chips","लेज़ चिप्स",2000,"pack",75,True),
    ],
    "personal_care": [
        ("Lifebuoy Soap","लाइफबॉय साबुन",4500,"piece",80,True),
        ("Head Shoulders","हेड शोल्डर्स",28000,"ml",50,True),
        ("Colgate","कोलगेट",9000,"gram",60,True),
    ],
}

GROCERY_BRANDS = [
    "Amul", "MDH", "Everest", "Shan", "Aashirvaad", "Britannia",
    "Parle", "Nestlé", "ITC", "Haldiram's", "Bikano", "Maggi",
    "Kissan", "Mother's Recipe", "Badshah", "Wagh Bakri", "Taj Mahal"
]

BROWSER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def new_id(prefix=""):
    """Generate unique IDs"""
    return f"{prefix}{uuid.uuid4().hex[:12]}"

def utcnow():
    """Get current UTC time"""
    return datetime.now(timezone.utc)

def random_past(min_days=1, max_days=180):
    """Random timestamp in the past"""
    days = random.randint(min_days, max_days)
    return utcnow() - timedelta(
        days=days,
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

def random_future(min_days=1, max_days=180):
    """Random timestamp in the future"""
    days = random.randint(min_days, max_days)
    return utcnow() + timedelta(
        days=days,
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

def random_amount(min_paise, max_paise):
    """Random amount in paise, rounded to nearest 50000"""
    raw = random.randint(min_paise, max_paise)
    return (raw // 50000) * 50000

def calculate_commission(gross_paise, commission_bps):
    """Calculate commission from gross amount and BPS"""
    return (gross_paise * commission_bps) // 10000

def vendor_net(gross_paise, commission_paise):
    """Calculate vendor net after commission"""
    return gross_paise - commission_paise

def fake_razorpay_order():
    """Generate fake Razorpay order ID"""
    return f"order_{uuid.uuid4().hex[:16]}"

def fake_razorpay_payment():
    """Generate fake Razorpay payment ID"""
    return f"pay_{uuid.uuid4().hex[:16]}"

def fake_razorpay_refund():
    """Generate fake Razorpay refund ID"""
    return f"rfnd_{uuid.uuid4().hex[:16]}"

def fake_razorpay_payout():
    """Generate fake Razorpay payout ID"""
    return f"pout_{uuid.uuid4().hex[:16]}"

def fake_cloudinary_url(folder="images"):
    """Generate fake Cloudinary image URL"""
    return f"https://res.cloudinary.com/eventapp/{folder}/{uuid.uuid4().hex[:8]}.jpg"

def fake_ip():
    """Generate random IP address"""
    return f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"

def tag(doc):
    """Add safety tags to document"""
    doc["_is_test_data"] = True
    doc["_seed_tag"] = SEED_TAG
    doc["_seeded_at"] = utcnow()
    return doc

def batch_insert(docs, batch_size=50):
    """Yield documents in batches"""
    for i in range(0, len(docs), batch_size):
        yield docs[i:i + batch_size]

# ═══════════════════════════════════════════════════════════════════════════════
# SEED FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def seed_categories(db):
    """Seed vendor categories"""
    print("   🏷️  Seeding categories...")
    
    categories = []
    for config in VENDOR_CATEGORY_CONFIGS:
        doc = {
            "_id": new_id("cat_"),
            "name": config["name"],
            "type": config["type"],
            "commission_bps": config["commission_bps"],
            "description": f"{config['name']} services for events",
            "icon_url": fake_cloudinary_url("categories"),
            "is_active": True,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
        categories.append(tag(doc))
    
    await db.vendor_categories.insert_many(categories)
    
    # Return as dict for lookup
    return {cat["type"]: cat for cat in categories}

async def seed_users(db):
    """Seed users: admin + customers + vendor users"""
    print("   👥 Seeding users (1 admin + 100 customers + 100 vendors)...")
    
    users = []
    
    # Admin user
    admin = {
        "_id": new_id("user_"),
        "email": "admin@eventapp.com",
        "password_hash": PASSWORD_HASH,
        "role": "admin",
        "first_name": "Admin",
        "last_name": "User",
        "phone": "+919999999999",
        "status": "active",
        "is_blocked": False,
        "is_email_verified": True,
        "profile_image_url": fake_cloudinary_url("avatars"),
        "preferences": {
            "language": "en",
            "notifications_enabled": True,
        },
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    users.append(tag(admin))
    
    # 100 customer users
    customer_statuses = ["active"] * 85 + ["active"] * 8 + ["inactive"] * 7
    random.shuffle(customer_statuses)
    
    customers = []
    for i in range(100):
        first_name = random.choice(INDIAN_FIRST_NAMES)
        last_name = random.choice(INDIAN_LAST_NAMES)
        status = customer_statuses[i]
        is_blocked = True if status == "active" and "blocked" in ["blocked"] * 8 else False
        
        customer = {
            "_id": new_id("user_"),
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@gmail.com",
            "password_hash": PASSWORD_HASH,
            "role": "customer",
            "first_name": first_name,
            "last_name": last_name,
            "phone": f"+919{random.randint(10000000, 99999999)}",
            "status": status,
            "is_blocked": is_blocked,
            "is_email_verified": status == "active",
            "city": random.choice(INDIAN_CITIES),
            "state": "",  # Will be filled based on city
            "profile_image_url": fake_cloudinary_url("avatars"),
            "preferences": {
                "language": "en",
                "notifications_enabled": True,
                "currency": "INR",
            },
            "created_at": random_past(30, 180),
            "updated_at": utcnow(),
        }
        customer["state"] = INDIAN_STATES.get(customer["city"], "")
        customers.append(tag(customer))
    
    # 100 vendor users
    vendors_users = []
    vendor_idx = 0
    for config in VENDOR_CATEGORY_CONFIGS:
        category_type = config["type"]
        # Distribute vendors by category
        if category_type == "photography":
            count = 25
        elif category_type == "catering":
            count = 20
        elif category_type == "decoration":
            count = 20
        elif category_type == "venue":
            count = 15
        elif category_type == "music":
            count = 10
        elif category_type == "makeup":
            count = 5
        elif category_type == "mehendi":
            count = 3
        else:  # transport
            count = 2
        
        for j in range(count):
            city = random.choice(INDIAN_CITIES)
            vendor_user = {
                "_id": new_id("user_"),
                "email": f"{category_type}.{city.lower()}.{j}@test.com",
                "password_hash": PASSWORD_HASH,
                "role": "vendor",
                "first_name": random.choice(INDIAN_FIRST_NAMES),
                "last_name": random.choice(INDIAN_LAST_NAMES),
                "phone": f"+919{random.randint(10000000, 99999999)}",
                "status": "active",
                "is_blocked": False,
                "is_email_verified": True,
                "city": city,
                "state": INDIAN_STATES.get(city, ""),
                "profile_image_url": fake_cloudinary_url("avatars"),
                "preferences": {
                    "language": "en",
                    "notifications_enabled": True,
                },
                "created_at": random_past(30, 180),
                "updated_at": utcnow(),
            }
            vendors_users.append(tag(vendor_user))
            vendor_idx += 1
    
    users.extend(customers)
    users.extend(vendors_users)
    
    for batch in batch_insert(users):
        await db.users.insert_many(batch)
    
    return {
        "admin": admin,
        "customers": customers,
        "vendor_users": vendors_users,
    }

async def seed_vendors(db, categories, vendor_users):
    """Seed vendors (one per vendor_user)"""
    print("   🏪 Seeding 100 vendors...")
    
    vendors = []
    vendor_statuses_all = (
        ["active"] * 75 +
        ["active"] * 10 +  # unverified
        ["pending"] * 10 +
        ["suspended"] * 5
    )
    random.shuffle(vendor_statuses_all)
    
    vendor_plans = (
        ["free"] * 35 +
        ["pro"] * 45 +
        ["enterprise"] * 20
    )
    random.shuffle(vendor_plans)
    
    vendor_idx = 0
    for config in VENDOR_CATEGORY_CONFIGS:
        category_type = config["type"]
        if category_type == "photography":
            count = 25
        elif category_type == "catering":
            count = 20
        elif category_type == "decoration":
            count = 20
        elif category_type == "venue":
            count = 15
        elif category_type == "music":
            count = 10
        elif category_type == "makeup":
            count = 5
        elif category_type == "mehendi":
            count = 3
        else:  # transport
            count = 2
        
        for j in range(count):
            vendor_user = vendor_users[vendor_idx]
            is_verified = vendor_statuses_all[vendor_idx] == "active" and random.random() > 0.11
            status = vendor_statuses_all[vendor_idx]
            
            # Business names by category
            if category_type == "photography":
                business_names = ["Sharma Photography", "Royal Moments", "Divine Clicks", "Picture Perfect", "Lens Studio"]
            elif category_type == "catering":
                business_names = ["Royal Caterers", "Taste Delight", "Flavors Kitchen", "Golden Spoon", "Feast Masters"]
            elif category_type == "decoration":
                business_names = ["Dream Decoration", "Elegance Events", "Festival Décor", "Color Works", "Bloom & Design"]
            elif category_type == "venue":
                business_names = ["Kapoor Grand Venue", "Palace Events", "Heritage Hall", "Sapphire Resort", "Crystal Banquet"]
            elif category_type == "music":
                business_names = ["DJ Beats", "Music Magic", "Sound Sphere", "Groove Masters", "Rhythmic Vibes"]
            elif category_type == "makeup":
                business_names = ["Glam Studio", "Beauty Boutique", "Makeup Dreams", "Face Art", "Glow Studio"]
            elif category_type == "mehendi":
                business_names = ["Mehendi Magic", "Artistic Henna", "Mehendi House", "Bridal Mehendi", "Henna Dreams"]
            else:
                business_names = ["Star Transport", "Journey Comfort", "Premium Rides", "Elite Transport", "City Travels"]
            
            business_name = f"{random.choice(business_names)} {vendor_user['city']}"
            base_price = random_amount(PRICE_RANGES[category_type][0], PRICE_RANGES[category_type][1])
            plan = vendor_plans[vendor_idx]
            
            vendor = {
                "_id": new_id("vendor_"),
                "user_id": vendor_user["_id"],
                "business_name": business_name,
                "category_type": category_type,
                "category_id": categories[category_type]["_id"],
                "city": vendor_user["city"],
                "state": vendor_user["state"],
                "address": f"{random.randint(1, 500)} {random.choice(['Street', 'Road', 'Lane'])}, {vendor_user['city']}",
                "pincode": f"{random.randint(100000, 999999)}",
                "latitude": random.uniform(8.0, 35.0),
                "longitude": random.uniform(68.0, 97.0),
                "phone": vendor_user["phone"],
                "email": vendor_user["email"],
                "description": f"Specialized in {config['name'].lower()} services with {random.randint(5, 20)} years experience",
                "base_price_paise": base_price,
                "status": status,
                "is_verified": is_verified,
                "plan": plan,
                "ai_copilot_enabled": plan in ["pro", "enterprise"],
                "rating": round(random.uniform(3.5, 5.0), 1) if status == "active" else 0,
                "total_reviews": random.randint(0, 150) if status == "active" else 0,
                "total_bookings": random.randint(0, 100) if status == "active" else 0,
                "bank_account": {
                    "holder_name": vendor_user["first_name"] + " " + vendor_user["last_name"],
                    "account_number": str(random.randint(10000000000000000, 99999999999999999)),
                    "ifsc_code": random.choice(["ICIC0000001", "HDFC0000001", "SBIN0000001", "AXIS0000001"]),
                    "verified": status == "active",
                },
                "pan": f"{random.randint(10000000000000, 99999999999999)}",
                "gstin": f"{random.randint(10000000000000, 99999999999999)}",
                "documents": {
                    "business_license": fake_cloudinary_url("docs"),
                    "pan_card": fake_cloudinary_url("docs"),
                    "bank_proof": fake_cloudinary_url("docs"),
                },
                "portfolio_images": [fake_cloudinary_url("portfolio") for _ in range(random.randint(3, 10))],
                "response_rate": random.uniform(0.7, 1.0) if status == "active" else 0,
                "average_response_time_minutes": random.randint(5, 120) if status == "active" else 0,
                "created_at": random_past(30, 180),
                "updated_at": utcnow(),
            }
            
            vendors.append(tag(vendor))
            vendor_idx += 1
    
    for batch in batch_insert(vendors):
        await db.vendors.insert_many(batch)
    
    return vendors

async def seed_booking_intents(db, customers, vendors):
    """Seed booking intents"""
    print("   📋 Seeding 250 booking intents...")
    
    active_verified_vendors = [v for v in vendors if v["status"] == "active" and v["is_verified"]]
    
    intents = []
    intent_statuses = (
        ["pending"] * 50 +
        ["payment_done"] * 150 +
        ["expired"] * 50
    )
    random.shuffle(intent_statuses)
    
    # Category-specific items
    items_by_category = {
        "photography": ["Candid Photography", "Pre-wedding Shoot", "Album Design", "Drone Photography", "HD Videography"],
        "catering": ["Veg Thali per plate", "Non-veg Thali", "Welcome Drinks", "Desserts", "Appetizers"],
        "decoration": ["Stage Decoration", "Floral Arrangements", "Lighting Setup", "Drape Management", "Garden Setup"],
        "venue": ["Hall Rental", "Setup Time", "Cleanup Charges", "Premium Seating", "Parking Spaces"],
        "music": ["DJ Services", "Sound System", "Lighting Set", "Amplifier System", "Dance Floor Setup"],
        "makeup": ["Bridal Makeup", "Guest Makeup", "Makeup Touch-up", "Nail Art", "Hair Styling"],
        "mehendi": ["Mehendi Artist", "Mehendi Setup", "Mehendi Designs", "Mehendi Music", "Mehendi Decorations"],
        "transport": ["Vehicle Rental", "Driver Service", "Fuel Charges", "Parking", "Toll Charges"],
    }
    
    for i in range(250):
        customer = random.choice(customers)
        vendor = random.choice(active_verified_vendors)
        status = intent_statuses[i]
        
        # Generate line items based on vendor's category
        items = random.sample(items_by_category.get(vendor["category_type"], []), k=random.randint(2, 5))
        
        intent = {
            "_id": new_id("intent_"),
            "customer_id": customer["_id"],
            "vendor_id": vendor["_id"],
            "category_type": vendor["category_type"],
            "event_type": random.choice(EVENT_TYPES),
            "event_date": random_future(5, 180),
            "event_location": f"{random.choice(INDIAN_CITIES)}, India",
            "guest_count": random.randint(10, 500),
            "items": items,
            "notes": random.choice([
                "Need urgent service",
                "Budget flexible",
                "First time booking",
                "Large event",
                "Intimate gathering",
            ]),
            "status": status,
            "ai_quote_used": random.random() < 0.4,
            "created_at": random_past(10, 120),
            "updated_at": utcnow(),
        }
        
        if status == "expired":
            intent["expired_at"] = intent["created_at"] + timedelta(days=7)
        
        intents.append(tag(intent))
    
    for batch in batch_insert(intents):
        await db.booking_intents.insert_many(batch)
    
    return intents

async def seed_bookings(db, intents, customers, vendors, categories):
    """Seed bookings from payment_done intents"""
    print("   💼 Seeding 200 bookings...")
    
    payment_done_intents = [i for i in intents if i["status"] == "payment_done"]
    k = min(200, len(payment_done_intents))
    bookings_from_intents = random.sample(payment_done_intents, k=k)
    
    booking_statuses = (
        ["payment_received"] * 40 +
        ["confirmed"] * 50 +
        ["completed"] * 60 +
        ["cancelled"] * 30 +
        ["disputed"] * 20
    )
    random.shuffle(booking_statuses)
    
    bookings = []
    for idx, intent in enumerate(bookings_from_intents):
        vendor = await db.vendors.find_one({"_id": intent["vendor_id"]})
        status = booking_statuses[idx]
        
        # Get commission from category
        category = categories[vendor["category_type"]]
        commission_bps = category["commission_bps"]
        
        gross_amount = random_amount(
            PRICE_RANGES[vendor["category_type"]][0],
            PRICE_RANGES[vendor["category_type"]][1]
        )
        commission_amount = calculate_commission(gross_amount, commission_bps)
        vendor_net_amount = vendor_net(gross_amount, commission_amount)
        
        created_at = random_past(5, 90)
        
        # Determine scheduled_at based on status
        if status == "completed":
            scheduled_at = created_at + timedelta(days=random.randint(1, 90))
        elif status in ["confirmed", "payment_received"]:
            scheduled_at = random_future(5, 60)
        else:  # cancelled, disputed
            scheduled_at = random.choice([created_at + timedelta(days=random.randint(1, 60)), random_future(5, 60)])
        
        booking = {
            "_id": new_id("booking_"),
            "intent_id": intent["_id"],
            "customer_id": intent["customer_id"],
            "vendor_id": vendor["_id"],
            "category_type": vendor["category_type"],
            "event_type": intent["event_type"],
            "event_date": intent["event_date"],
            "event_location": intent["event_location"],
            "guest_count": intent["guest_count"],
            "service_items": intent["items"],
            "status": status,
            "gross_amount_paise": gross_amount,
            "commission_bps": commission_bps,
            "commission_amount_paise": commission_amount,
            "vendor_net_paise": vendor_net_amount,
            "platformfee_paise": 0,
            "tax_amount_paise": 0,
            "total_amount_paise": gross_amount,
            "sla_deadline": created_at + timedelta(hours=24),
            "is_sla_breached": random.random() < 0.1,
            "risk_score": round(random.uniform(0.1, 0.9), 2),
            "lead_score": round(random.uniform(0.1, 0.9), 2),
            "ai_recommended": random.random() < 0.5,
            "scheduled_at": scheduled_at,
            "created_at": created_at,
            "updated_at": utcnow(),
        }
        
        # Add optional fields based on status
        if status == "completed":
            booking["completed_at"] = scheduled_at + timedelta(hours=random.randint(0, 8))
            booking["rating"] = random.randint(3, 5)
            booking["review"] = random.choice([
                "Great service!",
                "Highly professional team",
                "Worth every rupee",
                "Perfect execution",
                "Exceeded expectations",
            ])
        elif status == "cancelled":
            booking["cancelled_at"] = random_past(1, 60)
            booking["cancellation_reason"] = random.choice(REFUND_REASONS)
            booking["cancelled_by"] = random.choice(["customer", "vendor", "admin"])
        elif status == "disputed":
            booking["disputed_at"] = scheduled_at + timedelta(hours=random.randint(1, 72))
            booking["dispute_reason"] = random.choice(DISPUTE_REASONS)
            booking["dispute_raised_by"] = random.choice(["customer", "vendor"])
        
        bookings.append(tag(booking))
    
    for batch in batch_insert(bookings):
        await db.bookings.insert_many(batch)
    
    return bookings

async def seed_payments(db, bookings, intents):
    """Seed payments for bookings"""
    print("   💳 Seeding payments...")
    
    payments = {}
    payment_docs = []
    
    for booking in bookings:
        status_map = {
            "completed": "confirmed",
            "confirmed": "confirmed",
            "payment_received": "confirmed",
            "cancelled": "refunded",
            "disputed": random.choice(["confirmed", "refunded"]),
        }
        
        payment_status = status_map.get(booking["status"], "confirmed")
        
        payment = {
            "_id": new_id("payment_"),
            "booking_id": booking["_id"],
            "customer_id": booking["customer_id"],
            "vendor_id": booking["vendor_id"],
            "amount_paise": booking["total_amount_paise"],
            "currency": "INR",
            "method": random.choice(PAYMENT_METHODS),
            "status": payment_status,
            "razorpay_order_id": fake_razorpay_order(),
        }
        
        if payment_status == "confirmed":
            payment["razorpay_payment_id"] = fake_razorpay_payment()
            payment["confirmed_at"] = booking["created_at"] + timedelta(minutes=random.randint(1, 30))
        
        if payment_status == "refunded":
            payment["refunded_at"] = booking.get("cancelled_at") or booking.get("disputed_at")
        
        payment["created_at"] = booking["created_at"]
        payment["updated_at"] = utcnow()
        
        payments[booking["_id"]] = payment
        payment_docs.append(tag(payment))
    
    for batch in batch_insert(payment_docs):
        await db.payments.insert_many(batch)
    
    return payments

async def seed_vendor_ledger(db, bookings, vendors, payments):
    """Seed vendor ledger with cumulative balances"""
    print("   📊 Seeding vendor ledger...")
    
    ledger_docs = []
    vendor_balances = {}  # Track cumulative balance per vendor
    
    # Sort bookings by created_at for proper chronological processing
    sorted_bookings = sorted(bookings, key=lambda b: b["created_at"])
    
    for booking in sorted_bookings:
        vendor_id = booking["vendor_id"]
        
        # Initialize running balance for vendor if needed
        if vendor_id not in vendor_balances:
            vendor_balances[vendor_id] = 0
        
        # Only create ledger entry for certain statuses
        if booking["status"] in ["confirmed", "completed", "payment_received", "disputed"]:
            vendor_balances[vendor_id] += booking["vendor_net_paise"]
            
            ledger = {
                "_id": new_id("ledger_"),
                "vendor_id": vendor_id,
                "booking_id": booking["_id"],
                "transaction_type": "booking_earned",
                "amount_paise": booking["vendor_net_paise"],
                "running_balance_paise": vendor_balances[vendor_id],
                "description": f"Earnings from {booking['category_type']} booking",
                "created_at": booking["created_at"],
            }
            ledger_docs.append(tag(ledger))
    
    # Add payout entries (negative)
    payouts = await db.payouts.find({"status": {"$in": ["processing", "processed"]}}).to_list(None)
    for payout in payouts:
        vendor_id = payout["vendor_id"]
        
        if vendor_id not in vendor_balances:
            vendor_balances[vendor_id] = 0
        
        vendor_balances[vendor_id] -= payout["amount_paise"]
        
        ledger = {
            "_id": new_id("ledger_"),
            "vendor_id": vendor_id,
            "payout_id": payout["_id"],
            "transaction_type": "payout_processed",
            "amount_paise": -payout["amount_paise"],
            "running_balance_paise": vendor_balances[vendor_id],
            "description": f"Payout {payout['status']}",
            "created_at": payout.get("processed_at", payout["created_at"]),
        }
        ledger_docs.append(tag(ledger))
    
    # Re-sort by created_at before inserting (ensure all datetimes are timezone-aware)
    def ensure_aware(dt):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    ledger_docs = sorted(ledger_docs, key=lambda x: ensure_aware(x["created_at"]))
    
    for batch in batch_insert(ledger_docs):
        await db.vendor_ledger.insert_many(batch)

async def seed_payouts(db, bookings, vendors):
    """Seed payouts (completed bookings only)"""
    print("   💸 Seeding payouts...")
    
    admin = await db.users.find_one({"role": "admin", "_seed_tag": SEED_TAG})
    
    completed_bookings = [b for b in bookings if b["status"] == "completed"]
    payouts = []
    
    payout_statuses = (
        ["pending"] * 20 +
        ["approved"] * 15 +
        ["processing"] * 5 +
        ["processed"] * 15 +
        ["failed"] * 5
    )
    random.shuffle(payout_statuses)
    
    for idx, booking in enumerate(completed_bookings):
        status = payout_statuses[idx]
        
        payout = {
            "_id": new_id("payout_"),
            "vendor_id": booking["vendor_id"],
            "amount_paise": booking["vendor_net_paise"],
            "currency": "INR",
            "status": status,
            "bank_account": {
                "holder_name": "Vendor Bank Account",
                "account_number": str(random.randint(10000000000000000, 99999999999999999)),
                "ifsc_code": random.choice(["ICIC0000001", "HDFC0000001", "SBIN0000001", "AXIS0000001"]),
            },
            "created_at": booking["completed_at"] + timedelta(hours=random.randint(1, 24)),
        }
        
        if status in ["approved", "processing", "processed", "failed"]:
            payout["approved_at"] = payout["created_at"] + timedelta(hours=random.randint(1, 24))
            payout["approved_by"] = admin["_id"]
        
        if status in ["processing", "processed"]:
            payout["razorpay_payout_id"] = fake_razorpay_payout()
            payout["processed_at"] = payout["approved_at"] + timedelta(hours=random.randint(1, 48))
        
        payout["updated_at"] = utcnow()
        
        payouts.append(tag(payout))
    
    for batch in batch_insert(payouts):
        await db.payouts.insert_many(batch)
    
    return payouts

async def seed_refunds(db, bookings, payments):
    """Seed refunds for cancelled and disputed bookings"""
    print("   ↩️  Seeding refunds...")
    
    refundable_bookings = [b for b in bookings if b["status"] in ["cancelled", "disputed"]]
    refunds = []
    
    refund_statuses = (
        ["completed"] * 20 +
        ["processing"] * 15 +
        ["requested"] * 10 +
        ["failed"] * 5
    )
    random.shuffle(refund_statuses)
    
    for idx, booking in enumerate(refundable_bookings):
        status = refund_statuses[idx]
        
        # Calculate refund amount (80-90% of gross)
        refund_percentage = random.randint(80, 90)
        refund_amount = (booking["total_amount_paise"] * refund_percentage) // 100
        cancellation_fee = booking["total_amount_paise"] - refund_amount
        
        refund = {
            "_id": new_id("refund_"),
            "booking_id": booking["_id"],
            "payment_id": payments[booking["_id"]]["_id"],
            "customer_id": booking["customer_id"],
            "vendor_id": booking["vendor_id"],
            "gross_amount_paise": booking["total_amount_paise"],
            "refund_amount_paise": refund_amount,
            "cancellation_fee_paise": cancellation_fee,
            "currency": "INR",
            "status": status,
            "reason": random.choice(REFUND_REASONS),
            "initiated_by": random.choice(["customer"] * 8 + ["admin"] * 2) if booking["status"] == "disputed" else "customer",
            "created_at": booking.get("cancelled_at") or booking.get("disputed_at"),
        }
        
        if status == "completed":
            refund["razorpay_refund_id"] = fake_razorpay_refund()
            refund["completed_at"] = refund["created_at"] + timedelta(hours=random.randint(1, 72))
        elif status == "processing":
            refund["razorpay_refund_id"] = fake_razorpay_refund()
        
        refund["updated_at"] = utcnow()
        
        refunds.append(tag(refund))
    
    for batch in batch_insert(refunds):
        await db.refunds.insert_many(batch)
    
    return refunds

async def seed_webhooks(db, payments, refunds, payouts):
    """Seed webhook events"""
    print("   🔗 Seeding webhook events...")
    
    webhooks = []
    
    # Payment webhooks
    for payment in payments.values():
        if payment["status"] == "confirmed":
            webhook = {
                "_id": new_id("webhook_"),
                "event_type": "payment.captured",
                "data": {
                    "payment_id": payment["razorpay_payment_id"],
                    "order_id": payment["razorpay_order_id"],
                    "amount": payment["amount_paise"],
                },
                "processing_time_ms": random.randint(50, 500),
                "retry_count": 0,
                "status": "success",
                "created_at": payment["confirmed_at"] + timedelta(milliseconds=random.randint(100, 1000)),
            }
            webhooks.append(tag(webhook))
    
    # Failed payment webhooks
    for _ in range(10):
        webhook = {
            "_id": new_id("webhook_"),
            "event_type": "payment.failed",
            "data": {
                "payment_id": fake_razorpay_payment(),
                "order_id": fake_razorpay_order(),
                "amount": random.randint(500000, 50000000),
                "reason": random.choice(["Insufficient funds", "Card declined", "Network error"]),
            },
            "processing_time_ms": random.randint(50, 500),
            "retry_count": random.randint(1, 3),
            "status": "failed",
            "created_at": random_past(1, 60),
        }
        webhooks.append(tag(webhook))
    
    # Refund webhooks
    for refund in refunds:
        if refund["status"] == "completed":
            webhook = {
                "_id": new_id("webhook_"),
                "event_type": "refund.created",
                "data": {
                    "refund_id": refund["razorpay_refund_id"],
                    "payment_id": False,
                    "amount": refund["refund_amount_paise"],
                },
                "processing_time_ms": random.randint(50, 500),
                "retry_count": 0,
                "status": "success",
                "created_at": refund["completed_at"] + timedelta(milliseconds=random.randint(100, 1000)),
            }
            webhooks.append(tag(webhook))
    
    # Payout webhooks
    for payout in payouts:
        if payout["status"] == "processed":
            webhook = {
                "_id": new_id("webhook_"),
                "event_type": "payout.processed",
                "data": {
                    "payout_id": payout["razorpay_payout_id"],
                    "amount": payout["amount_paise"],
                    "vendor_id": payout["vendor_id"],
                },
                "processing_time_ms": random.randint(50, 500),
                "retry_count": 0,
                "status": "success",
                "created_at": payout["processed_at"] + timedelta(milliseconds=random.randint(100, 1000)),
            }
            webhooks.append(tag(webhook))
    
    for batch in batch_insert(webhooks):
        await db.webhook_events.insert_many(batch)
    
    return webhooks

async def seed_resource_locks(db, bookings, vendors):
    """Seed resource locks for bookings"""
    print("   🔒 Seeding resource locks...")
    
    locks = []
    
    for booking in bookings:
        status_map = {
            "payment_received": "active",
            "confirmed": "active",
            "completed": "released",
            "cancelled": "released",
            "disputed": "expired",
        }
        
        lock_status = status_map.get(booking["status"], "active")
        
        lock = {
            "_id": new_id("lock_"),
            "booking_id": booking["_id"],
            "vendor_id": booking["vendor_id"],
            "resource_type": "vendor_slot",
            "event_date": booking["event_date"],
            "locked_from": booking["created_at"],
            "locked_until": booking["scheduled_at"],
            "status": lock_status,
            "created_at": booking["created_at"],
        }
        
        if lock_status == "released":
            lock["released_at"] = booking.get("completed_at") or booking.get("cancelled_at")
        elif lock_status == "expired":
            lock["expired_at"] = booking.get("disputed_at")
        
        locks.append(tag(lock))
    
    for batch in batch_insert(locks):
        await db.resource_locks.insert_many(batch)
    
    return locks

async def seed_state_transitions(db, bookings, payments, refunds):
    """Seed state transitions for all entities"""
    print("   🔄 Seeding state transitions...")
    
    transitions = []
    
    # Booking state transitions
    for booking in bookings:
        if booking["status"] == "completed":
            # Progression: pending → payment_received → confirmed → completed
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "booking",
                "entity_id": booking["_id"],
                "previous_state": "pending",
                "new_state": "payment_received",
                "triggered_by": "system",
                "reason": "Payment received from customer",
                "created_at": booking["created_at"],
            }))
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "booking",
                "entity_id": booking["_id"],
                "previous_state": "payment_received",
                "new_state": "confirmed",
                "triggered_by": "vendor",
                "reason": "Vendor confirmed the booking",
                "created_at": booking["created_at"] + timedelta(hours=random.randint(1, 12)),
            }))
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "booking",
                "entity_id": booking["_id"],
                "previous_state": "confirmed",
                "new_state": "completed",
                "triggered_by": "system",
                "reason": "Event completed successfully",
                "created_at": booking["completed_at"],
            }))
        elif booking["status"] == "confirmed":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "booking",
                "entity_id": booking["_id"],
                "previous_state": "pending",
                "new_state": "payment_received",
                "triggered_by": "system",
                "reason": "Payment received",
                "created_at": booking["created_at"],
            }))
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "booking",
                "entity_id": booking["_id"],
                "previous_state": "payment_received",
                "new_state": "confirmed",
                "triggered_by": "admin",
                "reason": "Admin confirmed booking",
                "created_at": booking["created_at"] + timedelta(hours=random.randint(1, 24)),
            }))
        elif booking["status"] == "payment_received":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "booking",
                "entity_id": booking["_id"],
                "previous_state": "pending",
                "new_state": "payment_received",
                "triggered_by": "system",
                "reason": "Payment received",
                "created_at": booking["created_at"],
            }))
        elif booking["status"] == "cancelled":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "booking",
                "entity_id": booking["_id"],
                "previous_state": "payment_received",
                "new_state": "cancelled",
                "triggered_by": booking.get("cancelled_by", "customer"),
                "reason": booking.get("cancellation_reason", "Booking cancelled"),
                "created_at": booking["cancelled_at"],
            }))
        elif booking["status"] == "disputed":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "booking",
                "entity_id": booking["_id"],
                "previous_state": "confirmed",
                "new_state": "disputed",
                "triggered_by": booking.get("dispute_raised_by", "customer"),
                "reason": booking.get("dispute_reason", "Dispute raised"),
                "created_at": booking["disputed_at"],
            }))
    
    # Payment state transitions
    for payment in payments.values():
        if payment["status"] == "confirmed":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "payment",
                "entity_id": payment["_id"],
                "previous_state": "created",
                "new_state": "confirmed",
                "triggered_by": "system",
                "reason": "Payment captured",
                "created_at": payment["confirmed_at"],
            }))
        elif payment["status"] == "refunded":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "payment",
                "entity_id": payment["_id"],
                "previous_state": "confirmed",
                "new_state": "refunded",
                "triggered_by": "system",
                "reason": "Refund processed",
                "created_at": payment["refunded_at"],
            }))
    
    # Refund state transitions
    for refund in refunds:
        if refund["status"] == "completed":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "refund",
                "entity_id": refund["_id"],
                "previous_state": "requested",
                "new_state": "completed",
                "triggered_by": "system",
                "reason": "Refund completed",
                "created_at": refund["completed_at"],
            }))
        elif refund["status"] == "processing":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "refund",
                "entity_id": refund["_id"],
                "previous_state": "requested",
                "new_state": "processing",
                "triggered_by": "system",
                "reason": "Refund processing",
                "created_at": refund["created_at"],
            }))
        elif refund["status"] == "requested":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "refund",
                "entity_id": refund["_id"],
                "previous_state": "pending",
                "new_state": "requested",
                "triggered_by": "customer",
                "reason": "Refund requested",
                "created_at": refund["created_at"],
            }))
        elif refund["status"] == "failed":
            transitions.append(tag({
                "_id": new_id("transition_"),
                "entity_type": "refund",
                "entity_id": refund["_id"],
                "previous_state": "processing",
                "new_state": "failed",
                "triggered_by": "system",
                "reason": "Refund failed",
                "created_at": refund["created_at"] + timedelta(hours=24),
            }))
    
    for batch in batch_insert(transitions):
        await db.state_transitions.insert_many(batch)
    
    return transitions

async def seed_notifications(db, users_data, bookings, refunds):
    """Seed notifications"""
    print("   🔔 Seeding notifications...")
    
    notifications = []
    
    customers = users_data["customers"]
    admin = users_data["admin"]
    
    # Booking notifications
    for booking in bookings:
        if booking["status"] == "confirmed":
            # Notify customer
            notifications.append(tag({
                "_id": new_id("notif_"),
                "user_id": booking["customer_id"],
                "type": "booking_confirmed",
                "title": "Your Booking is Confirmed!",
                "message": f"Your {booking['category_type']} booking for {booking['event_date'].strftime('%Y-%m-%d')} has been confirmed",
                "data": {"booking_id": booking["_id"]},
                "read": random.random() < 0.4,
                "created_at": booking["created_at"] + timedelta(hours=random.randint(1, 24)),
            }))
            # Notify vendor
            vendor = await db.vendors.find_one({"_id": booking["vendor_id"]})
            notifications.append(tag({
                "_id": new_id("notif_"),
                "user_id": vendor["user_id"],
                "type": "booking_confirmed",
                "title": "Booking Confirmed!",
                "message": f"A {booking['category_type']} booking is confirmed for {booking['event_date'].strftime('%Y-%m-%d')}",
                "data": {"booking_id": booking["_id"]},
                "read": random.random() < 0.4,
                "created_at": booking["created_at"] + timedelta(hours=random.randint(1, 24)),
            }))
        
        elif booking["status"] == "completed":
            # Review request notification
            notifications.append(tag({
                "_id": new_id("notif_"),
                "user_id": booking["customer_id"],
                "type": "review_requested",
                "title": "Please Review Your Experience",
                "message": "We'd love to know about your experience with this vendor",
                "data": {"booking_id": booking["_id"]},
                "read": random.random() < 0.4,
                "created_at": booking["completed_at"] + timedelta(hours=random.randint(1, 48)),
            }))
        
        elif booking["status"] == "cancelled":
            # Notify both parties
            notifications.append(tag({
                "_id": new_id("notif_"),
                "user_id": booking["customer_id"],
                "type": "booking_cancelled",
                "title": "Booking Cancelled",
                "message": f"Your {booking['category_type']} booking has been cancelled",
                "data": {"booking_id": booking["_id"]},
                "read": random.random() < 0.4,
                "created_at": booking["cancelled_at"],
            }))
    
    # Refund notifications
    for refund in refunds:
        if refund["status"] == "completed":
            notifications.append(tag({
                "_id": new_id("notif_"),
                "user_id": refund["customer_id"],
                "type": "refund_processed",
                "title": "Refund Processed",
                "message": f"Refund of ₹{refund['refund_amount_paise']/100} has been processed",
                "data": {"refund_id": refund["_id"]},
                "read": random.random() < 0.4,
                "created_at": refund["completed_at"],
            }))
    
    # Promo offers (random customers)
    random_customers = random.sample(customers, k=50)
    for customer in random_customers:
        notifications.append(tag({
            "_id": new_id("notif_"),
            "user_id": customer["_id"],
            "type": "promo_offer",
            "title": "Exclusive Offer for You!",
            "message": f"Get {random.choice([10, 15, 20])}% discount on your next booking",
            "data": {"promo_code": f"SAVE{random.randint(100, 999)}"},
            "read": random.random() < 0.4,
            "created_at": random_past(1, 90),
        }))
    
    # SLA breach notifications to admin
    sla_breached = [b for b in bookings if b.get("is_sla_breached")]
    for booking in sla_breached[:20]:  # Sample
        notifications.append(tag({
            "_id": new_id("notif_"),
            "user_id": admin["_id"],
            "type": "sla_breach",
            "title": "SLA Breach Alert",
            "message": f"Booking {booking['_id']} exceeded SLA deadline",
            "data": {"booking_id": booking["_id"]},
            "read": random.random() < 0.4,
            "created_at": booking["sla_deadline"] + timedelta(hours=1),
        }))
    
    for batch in batch_insert(notifications):
        await db.notifications.insert_many(batch)
    
    return notifications

async def seed_audit_logs(db, admin, vendors, payouts, refunds, bookings, customers):
    """Seed audit logs"""
    print("   📋 Seeding audit logs...")
    
    logs = []
    
    # Vendor approval logs
    for _ in range(30):
        vendor = random.choice(vendors)
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "vendor_approved",
            "admin_id": admin["_id"],
            "resource_type": "vendor",
            "resource_id": vendor["_id"],
            "changes": {"status": "pending -> active"},
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": "Verified documentation and application",
            "created_at": random_past(30, 180),
        }))
    
    # Payout approval logs
    for _ in range(25):
        payout = random.choice(payouts)
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "payout_approved",
            "admin_id": admin["_id"],
            "resource_type": "payout",
            "resource_id": payout["_id"],
            "changes": {"status": "pending -> approved"},
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": "Funds verified and ready for processing",
            "created_at": random_past(30, 180),
        }))
    
    # Refund approval logs
    for _ in range(15):
        refund = random.choice(refunds)
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "refund_approved",
            "admin_id": admin["_id"],
            "resource_type": "refund",
            "resource_id": refund["_id"],
            "changes": {"status": f"requested -> approved"},
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": "Refund justified, approved for processing",
            "created_at": random_past(30, 180),
        }))
    
    # Dispute resolution logs
    for _ in range(10):
        booking = random.choice([b for b in bookings if b["status"] == "disputed"])
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "dispute_resolved",
            "admin_id": admin["_id"],
            "resource_type": "booking",
            "resource_id": booking["_id"],
            "changes": {"dispute_status": "open -> resolved"},
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": "Evidence reviewed, resolution approved",
            "created_at": random_past(30, 180),
        }))
    
    # Booking cancellation logs
    for _ in range(10):
        booking = random.choice([b for b in bookings if b["status"] == "cancelled"])
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "booking_cancelled",
            "admin_id": admin["_id"],
            "resource_type": "booking",
            "resource_id": booking["_id"],
            "changes": {"status": "active -> cancelled"},
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": booking.get("cancellation_reason", "Admin cancelled"),
            "created_at": random_past(30, 180),
        }))
    
    # User block logs
    for _ in range(8):
        customer = random.choice(customers)
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "user_blocked",
            "admin_id": admin["_id"],
            "resource_type": "user",
            "resource_id": customer["_id"],
            "changes": {"is_blocked": "false -> true"},
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": random.choice(["Suspicious activity", "Multiple complaints", "Policy violation"]),
            "created_at": random_past(30, 180),
        }))
    
    # Vendor suspension logs
    for _ in range(7):
        vendor = random.choice(vendors)
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "vendor_suspended",
            "admin_id": admin["_id"],
            "resource_type": "vendor",
            "resource_id": vendor["_id"],
            "changes": {"status": "active -> suspended"},
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": random.choice(["Low quality complaints", "SLA breaches", "Payment fraud"]),
            "created_at": random_past(30, 180),
        }))
    
    # Commission override logs
    for _ in range(5):
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "commission_override",
            "admin_id": admin["_id"],
            "resource_type": "booking",
            "resource_id": random.choice(bookings)["_id"],
            "changes": {"commission_bps": f"{random.randint(800, 1500)} -> {random.randint(500, 1200)}"},
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": "Special approval for VIP vendor",
            "created_at": random_past(30, 180),
        }))
    
    # Platform config updates
    for _ in range(5):
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "platform_config_updated",
            "admin_id": admin["_id"],
            "resource_type": "platform",
            "resource_id": "config",
            "changes": {
                "setting": random.choice(["min_commission_bps", "max_sla_hours", "refund_percentage"]),
                "old_value": str(random.randint(500, 1500)),
                "new_value": str(random.randint(500, 1500)),
            },
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": "Configuration update approved",
            "created_at": random_past(30, 180),
        }))
    
    # Vendor rejection logs
    for _ in range(5):
        logs.append(tag({
            "_id": new_id("auditlog_"),
            "action": "vendor_rejected",
            "admin_id": admin["_id"],
            "resource_type": "vendor_application",
            "resource_id": new_id("vendor_"),
            "changes": {"status": "pending -> rejected"},
            "ip_address": fake_ip(),
            "user_agent": random.choice(BROWSER_AGENTS),
            "reason": random.choice(["Incomplete documentation", "Failed verification", "Policy violation"]),
            "created_at": random_past(30, 180),
        }))
    
    for batch in batch_insert(logs):
        await db.audit_logs.insert_many(batch)
    
    return logs

async def seed_grocery_items(db, vendors):
    """Seed grocery items"""
    print("   🛒 Seeding grocery items...")
    
    active_vendors = [v for v in vendors if v["status"] == "active" and v["is_verified"]]
    items = []
    
    for category, products in GROCERY_DATA.items():
        for name_en, name_hi, base_price, unit, stock, organic in products:
            vendor = random.choice(active_vendors)
            price_paise = base_price * 100  # Convert to paise
            mrp_paise = int(price_paise * random.uniform(1.1, 1.2))
            discount_percent = random.randint(5, 20)
            
            item = {
                "_id": new_id("item_"),
                "vendor_id": vendor["_id"],
                "category": category,
                "name_en": name_en,
                "name_hi": name_hi,
                "description": f"Fresh {name_en} from trusted supplier",
                "price_paise": price_paise,
                "mrp_paise": mrp_paise,
                "discount_percent": discount_percent,
                "unit": unit,
                "stock_quantity": stock,
                "brand": random.choice(GROCERY_BRANDS),
                "is_organic": organic or random.random() < 0.2,
                "is_available": True,
                "image_url": fake_cloudinary_url("grocery"),
                "tags": [category, "fresh", random.choice(["premium", "budget", "organic"])],
                "expiry_days": random.randint(30, 180) if category != "dairy" else random.randint(1, 30),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "total_reviews": random.randint(0, 200),
                "created_at": random_past(30, 180),
                "updated_at": utcnow(),
            }
            items.append(tag(item))
    
    for batch in batch_insert(items):
        await db.grocery_items.insert_many(batch)
    
    return items

async def seed_grocery_orders(db, customers, grocery_items, vendors):
    """Seed grocery orders"""
    print("   📦 Seeding grocery orders...")
    
    orders = []
    
    order_statuses = (
        ["delivered"] * 60 +
        ["out_for_delivery"] * 20 +
        ["packed"] * 15 +
        ["confirmed"] * 25 +
        ["pending"] * 15 +
        ["cancelled"] * 10 +
        ["returned"] * 5
    )
    random.shuffle(order_statuses)
    
    delivery_slots = ["Morning 6-10 AM", "Afternoon 12-4 PM", "Evening 6-9 PM"]
    
    for _ in range(150):
        customer = random.choice(customers)
        order_items = random.sample(grocery_items, k=random.randint(2, 8))
        status = order_statuses[len(orders) % len(order_statuses)]
        
        total_amount = sum(item["price_paise"] for item in order_items) * random.randint(1, 3)
        
        order = {
            "_id": new_id("order_"),
            "customer_id": customer["_id"],
            "items": [
                {
                    "item_id": item["_id"],
                    "vendor_id": item["vendor_id"],
                    "name": item["name_en"],
                    "price_paise": item["price_paise"],
                    "quantity": random.randint(1, 5),
                    "unit": item["unit"],
                }
                for item in order_items
            ],
            "total_amount_paise": total_amount,
            "tax_paise": int(total_amount * 0.05),
            "discount_paise": int(total_amount * random.uniform(0, 0.1)),
            "delivery_fee_paise": random.choice([0, 5000, 10000, 15000]),
            "final_amount_paise": total_amount,
            "status": status,
            "payment_method": random.choice(["online", "online", "online", "online", "online", "online", "cod"]),
            "delivery_address": f"{random.randint(1, 500)} {random.choice(['Street', 'Road', 'Lane'])}, {customer['city']}, {customer['state']} {random.randint(100000, 999999)}",
            "delivery_slot": random.choice(delivery_slots),
            "notes": random.choice([
                "Handle with care",
                "Leave at door",
                "Call before delivery",
                "",
                "No special instructions",
            ]),
            "created_at": random_past(30, 180),
        }
        
        if status in ["delivered", "returned"]:
            order["delivered_at"] = order["created_at"] + timedelta(hours=random.randint(2, 48))
            order["rating"] = random.randint(3, 5)
            order["review"] = random.choice([
                "Fresh and on time",
                "Great quality",
                "Highly recommend",
                "Perfect delivery",
                "",
            ])
        elif status == "out_for_delivery":
            order["out_for_delivery_at"] = order["created_at"] + timedelta(hours=random.randint(1, 12))
        elif status == "packed":
            order["packed_at"] = order["created_at"] + timedelta(hours=random.randint(1, 6))
        elif status == "confirmed":
            order["confirmed_at"] = order["created_at"] + timedelta(hours=random.randint(0, 2))
        elif status == "cancelled":
            order["cancelled_at"] = order["created_at"] + timedelta(hours=random.randint(0, 12))
            order["cancellation_reason"] = random.choice([
                "Out of stock",
                "Item no longer available",
                "Customer requested",
            ])
        
        order["updated_at"] = utcnow()
        
        orders.append(tag(order))
    
    for batch in batch_insert(orders):
        await db.grocery_orders.insert_many(batch)
    
    return orders

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SEED FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

async def seed():
    """Main seed execution"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Duplicate check
    existing = await db.users.find_one({"email": "admin@eventapp.com", "_seed_tag": SEED_TAG})
    if existing:
        print("⚠️  Already seeded! Agar dobara seed karna hai toh pehle cleanup_test_data.py chalao.")
        client.close()
        return
    
    print("🚀 Seeding shuru ho raha hai...\n")
    
    try:
        categories   = await seed_categories(db)
        users_data   = await seed_users(db)
        vendors      = await seed_vendors(db, categories, users_data["vendor_users"])
        intents      = await seed_booking_intents(db, users_data["customers"], vendors)
        bookings     = await seed_bookings(db, intents, users_data["customers"], vendors, categories)
        payments     = await seed_payments(db, bookings, intents)
        payouts      = await seed_payouts(db, bookings, vendors)
        refunds      = await seed_refunds(db, bookings, payments)
        await seed_vendor_ledger(db, bookings, vendors, payments)
        await seed_webhooks(db, payments, refunds, payouts)
        await seed_resource_locks(db, bookings, vendors)
        transitions  = await seed_state_transitions(db, bookings, payments, refunds)
        await seed_notifications(db, users_data, bookings, refunds)
        await seed_audit_logs(db, users_data["admin"], vendors, payouts, refunds, bookings, users_data["customers"])
        grocery      = await seed_grocery_items(db, vendors)
        await seed_grocery_orders(db, users_data["customers"], grocery, vendors)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        client.close()
        return
    
    # Final Summary
    print("\n" + "═"*70)
    print("✅ SEED COMPLETE!")
    print("═"*70)
    
    collections = [
        "users","vendor_categories","vendors","booking_intents",
        "bookings","payments","vendor_ledger","payouts","refunds",
        "webhook_events","resource_locks","state_transitions",
        "notifications","audit_logs","grocery_items","grocery_orders"
    ]
    
    print("\n📊 COLLECTION COUNTS:")
    for col in collections:
        count = await db[col].count_documents({"_seed_tag": SEED_TAG})
        print(f"   {col:<25}: {count:>5}")
    
    print("\n🔐 LOGIN CREDENTIALS:")
    print("   👑 Admin    : admin@eventapp.com          | Admin@1234")
    
    # Print 5 sample customers
    custs = await db.users.find(
        {"role":"customer","_seed_tag":SEED_TAG}
    ).limit(5).to_list(5)
    for c in custs:
        print(f"   👤 Customer : {c['email']:<33} | Test@1234")
    
    # Print 5 sample vendors
    vends = await db.vendors.find(
        {"status":"active","_seed_tag":SEED_TAG}
    ).limit(5).to_list(5)
    for v in vends:
        print(f"   🏪 Vendor   : {v['business_name']:<33} | {v['city']}")
    
    print("\n📅 BOOKING STATUS:")
    for status in ["payment_received","confirmed","completed","cancelled","disputed"]:
        c = await db.bookings.count_documents({"status":status,"_seed_tag":SEED_TAG})
        print(f"   {status:<20}: {c:>3}")
    
    print("\n💰 PAYOUT STATUS:")
    for status in ["pending","approved","processing","processed","failed"]:
        c = await db.payouts.count_documents({"status":status,"_seed_tag":SEED_TAG})
        print(f"   {status:<20}: {c:>3}")
    
    print("\n🛒 GROCERY ORDER STATUS:")
    for status in ["delivered","out_for_delivery","packed","confirmed","pending","cancelled","returned"]:
        c = await db.grocery_orders.count_documents({"status":status,"_seed_tag":SEED_TAG})
        print(f"   {status:<20}: {c:>3}")
    
    print("\n🧹 CLEANUP COMMAND:")
    print("   python cleanup_test_data.py")
    print("═"*70 + "\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed())
