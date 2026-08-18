import os
import sys
import urllib.request
import django

# Force UTF-8 output encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from apps.products.models import Product, Category

PRODUCT_IMAGE_MAP = {
    "Cardamom Tea": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
    "Filter Coffee": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop&q=80",
    "Fresh Cold Coffee": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=600&auto=format&fit=crop&q=80",
    "Veg Puff": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
    "Egg Puff": "https://images.unsplash.com/photo-1509722747041-616f39b57569?w=600&auto=format&fit=crop&q=80",
    "Chicken Puff": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
    "Samosa (2 Pcs)": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
    "Pepsi 250ml": "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=600&auto=format&fit=crop&q=80",
    "Bovonto 250ml": "https://images.unsplash.com/photo-1581006852262-e4307cf6283a?w=600&auto=format&fit=crop&q=80",
    "7Up 250ml": "https://images.unsplash.com/photo-1625772299848-391b6a87d7b3?w=600&auto=format&fit=crop&q=80",
    "Mineral Water 1L": "https://images.unsplash.com/photo-1560023907-5f339617ea30?w=600&auto=format&fit=crop&q=80",
    "Lays Magic Masala": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=600&auto=format&fit=crop&q=80",
    "Kurkure Masala Munch": "https://images.unsplash.com/photo-1621447504864-d8686e12698c?w=600&auto=format&fit=crop&q=80",
    "Dairy Milk Silk 60g": "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=600&auto=format&fit=crop&q=80",
    "Hide & Seek Biscuit": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=600&auto=format&fit=crop&q=80",
    "Fresh Lime Juice": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&auto=format&fit=crop&q=80",
    "Fresh Mango Juice": "https://images.unsplash.com/photo-1546173159-315724a31696?w=600&auto=format&fit=crop&q=80",
    "Veg Cheese Burger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
    "Crispy Chicken Burger": "https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?w=600&auto=format&fit=crop&q=80",
    "Personal Corn Pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
    "Personal Chicken Pizza": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600&auto=format&fit=crop&q=80",
    "Large Family Pizza (12-inch)": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=600&auto=format&fit=crop&q=80",
    "Personal Cheese Pizza": "https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=600&auto=format&fit=crop&q=80",
    "Chocolate Brownie": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600&auto=format&fit=crop&q=80",
    "Custom Celebration Cake (1kg)": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=600&auto=format&fit=crop&q=80",
    "Catering Biryani Feast (20 Pax)": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80"
}

CATEGORY_IMAGE_MAP = {
    "Tea & Hot Beverages": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
    "Coffee Specials": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop&q=80",
    "Puffs & Savouries": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
    "Cool Drinks": "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=600&auto=format&fit=crop&q=80",
    "Fresh Juices": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&auto=format&fit=crop&q=80",
    "Chips & Crisps": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=600&auto=format&fit=crop&q=80",
    "Chocolates": "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=600&auto=format&fit=crop&q=80",
    "Biscuits": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=600&auto=format&fit=crop&q=80",
    "Gourmet Burgers": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
    "Italian Pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
    "Fast Food": "https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=600&auto=format&fit=crop&q=80",
    "Bakery & Desserts": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600&auto=format&fit=crop&q=80",
    "Special Catering Items": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
    "Mineral Water": "https://images.unsplash.com/photo-1560023907-5f339617ea30?w=600&auto=format&fit=crop&q=80",
    "Tea & Coffee": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
    "Snacks & Savouries": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
    "Fried Snacks": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
    "Cool Drinks & Juices": "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=600&auto=format&fit=crop&q=80",
    "Special Catering": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80"
}

def main():
    media_products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
    media_categories_dir = os.path.join(settings.MEDIA_ROOT, 'categories')
    os.makedirs(media_products_dir, exist_ok=True)
    os.makedirs(media_categories_dir, exist_ok=True)

    headers = {'User-Agent': 'Mozilla/5.0'}

    print("Downloading and assigning product images...")
    products = Product.objects.all()
    for p in products:
        url = PRODUCT_IMAGE_MAP.get(p.name)
        if not url:
            print(f"Skipping {p.name} (no URL in map)")
            continue

        filename = f"prod_{p.id}_{p.name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('&', 'and')}.jpg"
        filepath = os.path.join(media_products_dir, filename)

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp, open(filepath, 'wb') as f:
                f.write(resp.read())
            
            p.image = f"products/{filename}"
            p.save()
            print(f"  [SUCCESS] Product '{p.name}' -> {p.image.name}")
        except Exception as e:
            print(f"  [FAILED] Failed downloading for {p.name}: {e}")

    print("\nDownloading and assigning category images...")
    categories = Category.objects.all()
    for c in categories:
        url = CATEGORY_IMAGE_MAP.get(c.name)
        if not url:
            print(f"Skipping category {c.name} (no URL in map)")
            continue

        filename = f"cat_{c.id}_{c.name.lower().replace(' ', '_').replace('&', 'and')}.jpg"
        filepath = os.path.join(media_categories_dir, filename)

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp, open(filepath, 'wb') as f:
                f.write(resp.read())
            
            c.image = f"categories/{filename}"
            c.save()
            print(f"  [SUCCESS] Category '{c.name}' -> {c.image.name}")
        except Exception as e:
            print(f"  [FAILED] Failed downloading for category {c.name}: {e}")

    print("\n[COMPLETE] All product and category images processed.")

if __name__ == '__main__':
    main()
