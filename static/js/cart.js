// Modern Cart Functionality
let cartCount = 0;
let cartTotal = 0;

// Update cart display with modern animations
function updateCartDisplay(count, total) {
    cartCount = count;
    cartTotal = total;
    
    // Update cart count with animation
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = count;
        
        // Add pulse animation when count changes
        cartCountElement.style.animation = 'none';
        setTimeout(() => {
            cartCountElement.style.animation = 'pulse 0.5s ease-out';
        }, 10);
    }
}

// Show modern notification toast
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification-modern');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification-modern ${type}`;
    notification.innerHTML = `
        <div class="flex items-center">
            <div class="flex-shrink-0">
                ${type === 'success' ? 
                    '<svg class="w-6 h-6 text-emerald-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>' :
                  type === 'error' ? 
                    '<svg class="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>' :
                    '<svg class="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
                }
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium text-gray-900">${message}</p>
            </div>
            <div class="ml-auto pl-3">
                <button onclick="this.parentElement.parentElement.remove()" class="inline-flex text-gray-400 hover:text-gray-600">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Add item to cart with loading state
function addToCart(productId) {
    const button = event.target;
    const originalText = button.textContent;
    
    // Show loading state
    button.disabled = true;
    button.innerHTML = '<span class="inline-flex items-center"><span class="loading-modern mr-2"></span>Adding...</span>';
    
    fetch('/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartDisplay(data.cart_count, data.cart_total);
            showNotification('Product added to cart successfully!', 'success');
        } else {
            showNotification('Failed to add product to cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while adding to cart', 'error');
    })
    .finally(() => {
        // Restore button state
        button.disabled = false;
        button.textContent = originalText;
    });
}

// Update quantity with smooth transitions
function updateQuantity(productId, newQuantity) {
    if (newQuantity < 1) return;
    
    fetch('/update_quantity', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: newQuantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartDisplay(data.cart_count, data.cart_total);
            showNotification('Cart updated successfully', 'success');
            // Refresh page to show updated quantities
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Failed to update cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while updating cart', 'error');
    });
}

// Remove item with confirmation
function removeFromCart(productId) {
    if (confirm('Are you sure you want to remove this item from your cart?')) {
        fetch('/remove_from_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartDisplay(data.cart_count, data.cart_total);
                showNotification('Item removed from cart', 'success');
                // Refresh page to show updated cart
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showNotification('Failed to remove item from cart', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while removing item', 'error');
        });
    }
}

// Clear cart with confirmation
function clearCart() {
    if (confirm('Are you sure you want to clear your entire cart?')) {
        fetch('/clear_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartDisplay(0, 0);
                showNotification('Cart cleared successfully', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showNotification('Failed to clear cart', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while clearing cart', 'error');
        });
    }
}

// Hero Search Functionality
let searchTimeout;
const heroSearchInput = document.getElementById('hero-search-input');
const heroSearchResults = document.getElementById('hero-search-results');

function performSearch(query) {
    if (query.length < 2) {
        hideSearchResults();
        return;
    }
    
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(products => {
            displaySearchResults(products);
        })
        .catch(error => {
            console.error('Search error:', error);
            hideSearchResults();
        });
}

function formatCurrency(price) {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(price);
}

function displaySearchResults(products) {
    if (!products || products.length === 0) {
        heroSearchResults.innerHTML = `
            <div class="p-4 text-center text-gray-500">
                <svg class="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
                <p class="text-sm">No products found</p>
            </div>
        `;
    } else {
        heroSearchResults.innerHTML = products.map(product => `
            <a href="/product/${product.id}" class="block p-4 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0">
                <div class="flex items-center space-x-4">
                    <img src="${product.image || 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=60&h=60&fit=crop&crop=center'}" 
                         alt="${product.name}" 
                         class="w-16 h-16 object-cover rounded-lg shadow-sm">
                    <div class="flex-1 min-w-0">
                        <h3 class="text-sm font-semibold text-gray-900 truncate">${product.name}</h3>
                        <p class="text-sm text-gray-500">${product.category}</p>
                        <p class="text-lg font-bold text-amber-600">${formatCurrency(product.price)}</p>
                    </div>
                    <div class="flex-shrink-0">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                        </svg>
                    </div>
                </div>
            </a>
        `).join('');
    }
    
    heroSearchResults.classList.remove('hidden');
}

function hideSearchResults() {
    heroSearchResults.classList.add('hidden');
}

// Hero search event listeners
if (heroSearchInput) {
    heroSearchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => performSearch(query), 300);
        } else {
            hideSearchResults();
        }
    });
    
    heroSearchInput.addEventListener('focus', function() {
        if (this.value.trim().length >= 2) {
            performSearch(this.value.trim());
        }
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', function(e) {
        if (!heroSearchInput.contains(e.target) && !heroSearchResults.contains(e.target)) {
            hideSearchResults();
        }
    });
    
    // Hide results on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideSearchResults();
            heroSearchInput.blur();
        }
    });
}

// Initialize cart on page load
document.addEventListener('DOMContentLoaded', function() {
    // Fetch initial cart state
    fetch('/get_cart_count')
        .then(response => response.json())
        .then(data => {
            updateCartDisplay(data.count || 0, data.total || 0);
        })
        .catch(error => {
            console.error('Error fetching cart state:', error);
            updateCartDisplay(0, 0);
        });
});

// Add slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
