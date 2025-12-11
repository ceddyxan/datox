from flask import session
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from data.products import Product

@dataclass
class CartItem:
    id: str
    name: str
    price: float
    image: str
    category: str
    quantity: int = 1

class CartManager:
    CART_KEY = 'cart'
    
    def __init__(self):
        pass
    
    def get_cart(self) -> List[CartItem]:
        """Get cart items from session"""
        cart_data = session.get(self.CART_KEY, [])
        return [CartItem(**item_data) for item_data in cart_data]
    
    def add_item(self, product: Product) -> None:
        """Add item to cart"""
        cart = self.get_cart()
        
        # Check if item already exists
        for item in cart:
            if item.id == product.id:
                item.quantity += 1
                break
        else:
            # Add new item
            cart.append(CartItem(
                id=product.id,
                name=product.name,
                price=product.price,
                image=product.image,
                category=product.category,
                quantity=1
            ))
        
        # Save to session
        session[self.CART_KEY] = [asdict(item) for item in cart]
    
    def remove_item(self, product_id: str) -> None:
        """Remove item from cart"""
        cart = self.get_cart()
        cart = [item for item in cart if item.id != product_id]
        session[self.CART_KEY] = [asdict(item) for item in cart]
    
    def update_quantity(self, product_id: str, quantity: int) -> None:
        """Update item quantity"""
        cart = self.get_cart()
        
        if quantity <= 0:
            self.remove_item(product_id)
            return
            
        for item in cart:
            if item.id == product_id:
                item.quantity = quantity
                break
                
        session[self.CART_KEY] = [asdict(item) for item in cart]
    
    def clear_cart(self) -> None:
        """Clear all items from cart"""
        session[self.CART_KEY] = []
    
    def get_total_count(self) -> int:
        """Get total number of items in cart"""
        cart = self.get_cart()
        return sum(item.quantity for item in cart)
    
    def get_total_price(self) -> float:
        """Get total price of items in cart"""
        cart = self.get_cart()
        return sum(item.price * item.quantity for item in cart)
    
    def get_item_count(self, product_id: str) -> int:
        """Get quantity of specific item in cart"""
        cart = self.get_cart()
        for item in cart:
            if item.id == product_id:
                return item.quantity
        return 0
