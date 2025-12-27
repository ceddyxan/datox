from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from data.products import (
    get_best_sellers, get_featured_products, get_products_by_category, get_product_by_id
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


def normalize_phone_number(raw):
    """Normalize Kenyan phone numbers to local 10-digit format (07XXXXXXXX).

    Accepts formats: 07XXXXXXXX, 7XXXXXXXX, 2547XXXXXXXX, +2547XXXXXXXX
    Returns normalized string like '07XXXXXXXX' or raises ValueError.
    """
    if not raw:
        raise ValueError('Empty phone number')
    digits = ''.join(ch for ch in str(raw) if ch.isdigit())

    # Local
    import re
    if re.match(r'^07\d{8}$', digits):
        return digits
    # shorthand 7XXXXXXXX
    if re.match(r'^7\d{8}$', digits):
        return '0' + digits
    # international 2547XXXXXXXX
    if re.match(r'^2547\d{8}$', digits):
        return '0' + digits[3:]
    # If plus sign was included, we've stripped it so same rules apply
    raise ValueError('Invalid Kenyan phone number')

def handle_image_upload(image_file, counter=None):
    """Handle image file upload and return URL"""
    # Validate file object
    if not image_file:
        print("DEBUG handle_image_upload: No file object provided")
        return None
    
    # Check filename
    if not hasattr(image_file, 'filename') or not image_file.filename:
        print("DEBUG handle_image_upload: File has no filename")
        return None
    
    filename = image_file.filename.strip()
    if not filename:
        print("DEBUG handle_image_upload: Filename is empty")
        return None
    
    # Check file extension
    if not allowed_file(filename):
        print(f"DEBUG handle_image_upload: File extension not allowed: {filename}")
        return None
    
    try:
        # Create upload directory if it doesn't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # Generate secure filename with timestamp, microsecond, and counter for uniqueness
        base_filename = secure_filename(filename)
        # Get file extension
        file_ext = os.path.splitext(base_filename)[1] or '.jpg'
        base_name = os.path.splitext(base_filename)[0] or 'image'
        
        # Use microsecond precision for uniqueness, plus counter to ensure no collisions
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        microseconds = now.microsecond
        
        # Create unique filename - counter ensures uniqueness even if microseconds collide
        if counter is not None:
            filename = f"{timestamp}_{microseconds:06d}_{counter:03d}_{base_name}{file_ext}"
        else:
            # Use a random component if no counter provided
            import random
            random_suffix = random.randint(1000, 9999)
            filename = f"{timestamp}_{microseconds:06d}_{random_suffix}_{base_name}{file_ext}"
        
        # Ensure filename doesn't already exist (add increment if needed)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        increment = 0
        while os.path.exists(filepath):
            increment += 1
            name_part = f"{timestamp}_{microseconds:06d}_{counter if counter is not None else random_suffix:03d}_{increment:03d}_{base_name}"
            filename = f"{name_part}{file_ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file - ensure stream is at beginning
        if hasattr(image_file, 'stream') and hasattr(image_file.stream, 'seek'):
            image_file.stream.seek(0)
        
        image_file.save(filepath)
        print(f"DEBUG handle_image_upload: Successfully saved {filename} to {filepath}")
        
        return f'uploads/{filename}'
    except Exception as e:
        print(f"DEBUG handle_image_upload: Exception saving file: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
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
                         best_sellers=get_best_sellers(), 
                         featured_products=get_featured_products(),
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


@app.route('/place_order', methods=['POST'])
def place_order():
    """Accept order data, normalize phones, save a simple order record, and clear the cart."""
    try:
        data = request.get_json() or {}
        full_name = (data.get('full_name') or '').strip()
        email = (data.get('email') or '').strip()
        phone_raw = (data.get('phone') or '').strip()
        mpesa_raw = (data.get('mpesa_phone') or '').strip()
        address = (data.get('address') or '').strip()
        notes = (data.get('notes') or '').strip()

        # Normalize phone(s)
        try:
            phone = normalize_phone_number(phone_raw)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid phone number'}), 400

        mpesa_phone = ''
        if mpesa_raw:
            try:
                mpesa_phone = normalize_phone_number(mpesa_raw)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid M-Pesa phone number'}), 400

        # Build order object
        order = {
            'id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'mpesa_phone': mpesa_phone,
            'address': address,
            'notes': notes,
            'items': cart_manager.get_cart(),
            'total': cart_manager.get_total_price(),
            'created_at': datetime.now().isoformat()
        }

        # Save to orders.json (append)
        orders_file = 'orders.json'
        try:
            if os.path.exists(orders_file):
                with open(orders_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f) or []
            else:
                existing = []
        except Exception:
            existing = []

        existing.append(order)
        try:
            with open(orders_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2)
        except Exception as e:
            print('Error saving order:', e)

        # Clear the server-side cart
        cart_manager.clear_cart()

        return jsonify({'success': True})

    except Exception as e:
        print('Error in place_order:', str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

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
            
            # Get all uploaded image files - Flask's getlist returns all files with name='images'
            image_files = request.files.getlist('images')
            print(f"DEBUG: Total files from getlist('images'): {len(image_files)}")
            
            # Process all files from the list
            for idx, img_file in enumerate(image_files):
                if img_file and hasattr(img_file, 'filename'):
                    filename = img_file.filename
                    if filename and filename.strip():
                        print(f"DEBUG: Found file {idx}: {filename}")
                        if allowed_file(filename):
                            try:
                                image_url = handle_image_upload(img_file, counter=idx)
                                if image_url and not image_url.startswith('https://'):
                                    images.append(image_url)
                                    print(f"DEBUG: Successfully added image {idx}: {image_url}")
                                else:
                                    print(f"DEBUG: Image {idx} returned default URL, skipping")
                            except Exception as e:
                                print(f"DEBUG: Error uploading image {idx} ({filename}): {str(e)}")
                                import traceback
                                traceback.print_exc()
                                flash(f'Error uploading {filename}: {str(e)}', 'error')
                        else:
                            print(f"DEBUG: File {idx} has invalid extension: {filename}")
                    else:
                        print(f"DEBUG: File {idx} has empty filename")
                else:
                    print(f"DEBUG: File {idx} is None or has no filename attribute")
            
            # Handle single image upload for backward compatibility
            single_image = request.files.get('image')
            if single_image and single_image.filename and single_image.filename.strip():
                if allowed_file(single_image.filename):
                    try:
                        image_url = handle_image_upload(single_image, counter=len(images))
                        if image_url and not image_url.startswith('https://'):
                            images.append(image_url)
                            print(f"DEBUG: Successfully added single image: {image_url}")
                    except Exception as e:
                        print(f"DEBUG: Error uploading single image: {str(e)}")
                        flash(f'Error uploading single image: {str(e)}', 'error')
            
            print(f"DEBUG: Total images processed: {len(images)}")
            
            # If no images uploaded, use default
            if not images:
                images = ['https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=200&h=200&fit=crop&crop=center']
            else:
                # Ensure we have at least the primary image set
                if not any(img for img in images if not img.startswith('https://')):
                    flash('Warning: No valid images were uploaded. Using default image.', 'warning')
            
            # Get form data
            name = request.form.get('name')
            category = request.form.get('category')
            price = float(request.form.get('price'))
            description = request.form.get('description')
            in_stock = request.form.get('in_stock') == 'true'
            
            # Get sizes and colors (multiple values)
            sizes = [s.strip() for s in request.form.getlist('sizes') if s.strip()]
            colors = [c.strip() for c in request.form.getlist('colors') if c.strip()]
            
            # Load products first to ensure we have the latest data
            products = load_products()
            
            # Generate unique ID based on existing product IDs
            existing_ids = [int(p.get('id', 0)) for p in products if p.get('id', '').isdigit()]
            new_id = str(max(existing_ids, default=0) + 1) if existing_ids else '1'
            
            # Create new product
            product = {
                'id': new_id,
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
                image_url = handle_image_upload(single_image, counter=0)
                uploaded_images.append(image_url)
            
            # Process multiple images with counter to ensure uniqueness
            start_counter = len(uploaded_images)  # Start counter after single image if any
            for index, image_file in enumerate(image_files):
                if image_file and image_file.filename and allowed_file(image_file.filename):
                    image_url = handle_image_upload(image_file, counter=start_counter + index)
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
