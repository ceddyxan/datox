from dataclasses import dataclass
from typing import List, Optional

import json
import os

@dataclass
class Product:
    id: str
    name: str
    price: float
    image: str
    category: str
    description: Optional[str] = None
    in_stock: bool = True
    sizes: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    images: Optional[List[str]] = None

def load_json_products():
    """Load products from JSON file"""
    try:
        with open('products.json', 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            
            data = json.loads(content)
            return [
                Product(
                    id=item.get('id', ''),
                    name=item.get('name', ''),
                    price=item.get('price', 0.0),
                    image=item.get('image', ''),
                    category=item.get('category', ''),
                    description=item.get('description'),
                    in_stock=item.get('in_stock', True),
                    sizes=item.get('sizes', []),
                    colors=item.get('colors', []),
                    images=item.get('images', [])
                )
                for item in data
            ]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_all_products():
    """Get all products - always fresh from JSON"""
    return load_json_products()

def get_best_sellers():
    """Get best sellers - always fresh from JSON"""
    all_products = get_all_products()
    return all_products[:4] if len(all_products) >= 4 else all_products

def get_featured_products():
    """Get featured products - always fresh from JSON"""
    all_products = get_all_products()
    return all_products[4:8] if len(all_products) >= 8 else all_products[4:]

# Backwards compatibility
best_sellers = get_best_sellers()
featured_products = get_featured_products()

def get_products_by_category(category: str) -> List[Product]:
    """Get products by category (case-insensitive) - always fresh"""
    all_products = load_json_products()
    return [product for product in all_products 
            if product.category.lower() == category.lower()]

def get_product_by_id(product_id: str) -> Optional[Product]:
    """Get product by ID - always fresh"""
    all_products = load_json_products()
    for product in all_products:
        if product.id == product_id:
            return product
    return None

def get_all_categories() -> List[str]:
    """Get all unique categories - always fresh"""
    all_products = load_json_products()
    categories = set()
    for product in all_products:
        categories.add(product.category)
    return sorted(list(categories))

# Remove refresh function since data is always fresh
def refresh_products():
    """No longer needed - data is always fresh"""
    pass
