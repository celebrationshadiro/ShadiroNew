import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']


async def init_categories():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    categories = [
        {
            "id": "cat-venues",
            "name": "Event Venues",
            "slug": "venues",
            "description": "Beautiful venues for your special events",
            "icon": "Building2",
            "image_url": "https://images.unsplash.com/photo-1761110787206-2cc164e4913c"
        },
        {
            "id": "cat-wedding-planners",
            "name": "Wedding Planners",
            "slug": "wedding-planners",
            "description": "Professional wedding planning services",
            "icon": "Heart",
            "image_url": "https://images.unsplash.com/photo-1766910699971-2fb00922eefc"
        },
        {
            "id": "cat-makeup",
            "name": "Makeup Artists & Stylists",
            "slug": "makeup",
            "description": "Expert makeup artists and stylists",
            "icon": "Sparkles",
            "image_url": "https://images.unsplash.com/photo-1677691257237-3294c7fd18a5"
        },
        {
            "id": "cat-photography",
            "name": "Photographers & Videographers",
            "slug": "photography",
            "description": "Capture your precious moments",
            "icon": "Camera",
            "image_url": "https://images.unsplash.com/photo-1629120881990-0c5b979884bc"
        },
        {
            "id": "cat-decor",
            "name": "Decorators & Florists",
            "slug": "decor",
            "description": "Transform your venue with stunning decor",
            "icon": "Flower2",
            "image_url": "https://images.unsplash.com/photo-1769812343322-f4a6e73c8aa7"
        },
        {
            "id": "cat-catering",
            "name": "Caterers & Bakers",
            "slug": "catering",
            "description": "Delicious food for your guests",
            "icon": "UtensilsCrossed",
            "image_url": "https://images.unsplash.com/photo-1769638913609-aa66bedf24d9"
        },
        {
            "id": "cat-entertainment",
            "name": "DJs, Bands, & Entertainers",
            "slug": "entertainment",
            "description": "Keep your guests entertained",
            "icon": "Music",
            "image_url": "https://images.unsplash.com/photo-1663668567002-6190b578c308"
        },
        {
            "id": "cat-transport",
            "name": "Transport & Rental Services",
            "slug": "transport",
            "description": "Luxury transport and rental services",
            "icon": "Car",
            "image_url": "https://images.unsplash.com/photo-1761671612738-2ac97bc59141"
        },
        {
            "id": "cat-mehandi",
            "name": "Mehandi Designer",
            "slug": "mehandi",
            "description": "Beautiful mehandi designs",
            "icon": "Hand",
            "image_url": "https://images.unsplash.com/photo-1674884060571-96a46a9a7a72"
        },
        {
            "id": "cat-grocery",
            "name": "Grocery Vendors",
            "slug": "grocery",
            "description": "Fresh groceries and supplies for your events",
            "icon": "ShoppingBag",
            "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e"
        }
    ]
    
    existing = await db.vendor_categories.count_documents({})
    if existing == 0:
        await db.vendor_categories.insert_many(categories)
        print(f"✅ Inserted {len(categories)} vendor categories")
    else:
        print(f"✓ Categories already exist ({existing} found)")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(init_categories())
