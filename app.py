from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from data.products import (
    best_sellers, featured_products, get_products_by_category, get_product_by_id
)
from utils.cart import CartManager

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Custom filter for currency formatting
@app.template_filter('currency_format')
def currency_format(value):
    if value is None:
        return "0.00"
    
    # Convert to Decimal for precise rounding
    try:
        decimal_value = Decimal(str(value))
        # Round to 2 decimal places
        rounded = decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        # Format with commas and 2 decimal places
        formatted = "{:,.2f}".format(rounded)
        return formatted
    except (ValueError, TypeError):
        return "0.00"

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize cart manager
cart_manager = CartManager()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_image_upload(image_file):
    """Handle image file upload and return URL"""
    if not image_file or not allowed_file(image_file.filename):
        return 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=200&h=200&fit=crop&crop=center'
    
    # Create upload directory if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Generate secure filename with timestamp
    filename = secure_filename(image_file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    
    # Save file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file.save(filepath)
    
    return f'uploads/{filename}'
def load_products():
    """Load products from JSON file"""
    try:
        with open('products.json', 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_products(products):
    """Save products to JSON file"""
    with open('products.json', 'w') as f:
        json.dump(products, f, indent=2)

@app.route('/')
def home():
    return render_template('home.html', 
                         best_sellers=best_sellers, 
                         featured_products=featured_products,
                         get_products_by_category=get_products_by_category)

@app.route('/products/<category>')
def category_page(category):
    # Try different category name formats
    category_variants = [
        category,
        category.replace('-', ' & '),
        category.replace('-', ' '),
        category.replace(' ', ' & '),
        category.replace(' & ', '-'),
        category.replace(' ', '-')
    ]
    
    for variant in category_variants:
        category_products = get_products_by_category(variant)
        if category_products:
            break
    else:
        category_products = []
    
    return render_template('category.html', 
                         category=category.replace('-', ' ').title(),
                         products=category_products)

@app.route('/product/<product_id>')
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return "Product not found", 404
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    cart_items = cart_manager.get_cart()
    subtotal = cart_manager.get_total_price()
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/get_cart_count')
def get_cart_count():
    return jsonify({
        'count': cart_manager.get_total_count(),
        'total': cart_manager.get_total_price()
    })

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.json.get('product_id')
    product = get_product_by_id(product_id)
    if product:
        cart_manager.add_item(product)
        return jsonify({
            'success': True,
            'cart_count': cart_manager.get_total_count(),
            'cart_total': cart_manager.get_total_price()
        })
    return jsonify({'success': False}), 404

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = request.json.get('product_id')
    cart_manager.remove_item(product_id)
    return jsonify({
        'success': True,
        'cart_count': cart_manager.get_total_count(),
        'cart_total': cart_manager.get_total_price()
    })

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)
    cart_manager.update_quantity(product_id, quantity)
    return jsonify({
        'success': True,
        'cart_count': cart_manager.get_total_count(),
        'cart_total': cart_manager.get_total_price()
    })

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    cart_manager.clear_cart()
    return jsonify({
        'success': True,
        'cart_count': 0,
        'cart_total': 0
    })

@app.route('/checkout')
def checkout():
    cart_items = cart_manager.get_cart()
    if not cart_items:
        return redirect(url_for('cart'))
    subtotal = cart_manager.get_total_price()
    return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Admin Routes
@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify([])
    
    products = load_products()
    filtered_products = []
    
    for product in products:
        if (query in product['name'].lower() or 
            query in product['description'].lower()):
            filtered_products.append(product)
    
    return jsonify(filtered_products[:8])  # Limit to 8 results

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard with product statistics"""
    products = load_products()
    
    # Calculate statistics
    total_products = len(products)
    in_stock_count = sum(1 for p in products if p.get('in_stock', True))
    out_of_stock_count = total_products - in_stock_count
    total_value = sum(p.get('price', 0) for p in products)
    
    return render_template('admin/dashboard.html', 
                         products=products,
                         total_products=total_products,
                         in_stock_count=in_stock_count,
                         out_of_stock_count=out_of_stock_count,
                         total_value=total_value)

@app.route('/admin/add-product', methods=['GET', 'POST'])
def add_product():
    """Add new product"""
    if request.method == 'POST':
        try:
            # Handle multiple image uploads
            images = []
            
            # Get all uploaded image files
            image_files = request.files.getlist('images')
            
            # Handle single image upload for backward compatibility
            single_image = request.files.get('image')
            if single_image and single_image.filename:
                image_files.append(single_image)
            
            # Process each image
            for image_file in image_files:
                if image_file and image_file.filename and allowed_file(image_file.filename):
                    image_url = handle_image_upload(image_file)
                    images.append(image_url)
            
            # If no images uploaded, use default
            if not images:
                images = ['https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=200&h=200&fit=crop&crop=center']
            
            # Get form data
            name = request.form.get('name')
            category = request.form.get('category')
            price = float(request.form.get('price'))
            description = request.form.get('description')
            in_stock = request.form.get('in_stock') == 'true'
            
            # Get sizes and colors (multiple values)
            sizes = [s.strip() for s in request.form.getlist('sizes') if s.strip()]
            colors = [c.strip() for c in request.form.getlist('colors') if c.strip()]
            
            # Create new product
            product = {
                'id': str(len(load_products()) + 1),
                'name': name,
                'category': category,
                'price': price,
                'description': description,
                'image': images[0] if images else '',  # Primary image
                'images': images,  # All images array
                'in_stock': in_stock,
                'sizes': sizes,
                'colors': colors,
                'created_at': datetime.now().isoformat()
            }
            
            # Save product
            products = load_products()
            products.append(product)
            save_products(products)
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'Error adding product: {str(e)}', 'error')
            return redirect(url_for('add_product'))
    
    return render_template('admin/add_product.html')

@app.route('/admin/delete-product/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete product"""
    try:
        products = load_products()
        products = [p for p in products if p['id'] != product_id]
        save_products(products)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/edit-product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """Edit existing product"""
    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return "Product not found", 404
    
    if request.method == 'POST':
        try:
            # Handle multiple image uploads
            uploaded_images = []
            image_files = request.files.getlist('images')
            
            # Handle single image upload for backward compatibility
            single_image = request.files.get('image')
            if single_image and single_image.filename and allowed_file(single_image.filename):
                image_url = handle_image_upload(single_image)
                uploaded_images.append(image_url)
            
            # Process multiple images
            for image_file in image_files:
                if image_file and allowed_file(image_file.filename):
                    image_url = handle_image_upload(image_file)
                    uploaded_images.append(image_url)
            
            # Handle removed images
            removed_images = request.form.get('removed_images', '').split(',')
            removed_images = [img for img in removed_images if img.strip()]
            
            # Update images array
            current_images = product.get('images', [])
            if not current_images and product.get('image'):
                current_images = [product['image']]
            
            # Remove specified images
            current_images = [img for img in current_images if img not in removed_images]
            
            # Add new uploaded images
            current_images.extend(uploaded_images)
            
            # Update the main image field if needed
            if current_images:
                product['image'] = current_images[0]
                product['images'] = current_images
            
            # Update product data
            product.update({
                'name': request.form.get('name'),
                'category': request.form.get('category'),
                'price': float(request.form.get('price')),
                'description': request.form.get('description'),
                'in_stock': request.form.get('in_stock') == 'true',
                'sizes': [s.strip() for s in request.form.getlist('sizes') if s.strip()],
                'colors': [c.strip() for c in request.form.getlist('colors') if c.strip()]
            })
            
            # Save updated products
            save_products(products)
            
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'Error updating product: {str(e)}', 'error')
            return redirect(url_for('edit_product', product_id=product_id))
    
    return render_template('admin/edit_product.html', product=product)

if __name__ == '__main__':
    app.run(debug=True)
