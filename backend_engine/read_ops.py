'''
Product operations for WeCare Beauty Store
Handles product loading, saving, and management
'''

import json
import os
from datetime import datetime
import threading
import time

# Global products dictionary with thread lock for synchronization
products = {}
products_lock = threading.Lock()
_last_update_time = 0
_update_interval = 2  # seconds between forced reloads

def get_products_file_path():
    """Get absolute path to products.json file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return os.path.join(parent_dir, 'database', 'products.json')

def get_database_dir():
    """Get absolute path to database directory"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return os.path.join(parent_dir, 'database')

def load_products(force=False):
    """Load products from JSON file - MAIN ENTRY POINT"""
    global products, _last_update_time
    
    current_time = time.time()
    
    # Only reload if forced or if enough time has passed (prevent infinite loops)
    if not force and (current_time - _last_update_time) < _update_interval:
        return True
        
    # Add a safety check to prevent too frequent reloads
    if (current_time - _last_update_time) < 0.5:  # Minimum 0.5 seconds between reloads
        return True
        
    print("🔄 Loading products from JSON file...")
    
    # ... rest of the function remains the same ...
    
    json_file = get_products_file_path()
    
    with products_lock:
        try:
            # Create database directory if it doesn't exist
            database_dir = os.path.dirname(json_file)
            if not os.path.exists(database_dir):
                os.makedirs(database_dir)
                print(f"✅ Created database directory: {database_dir}")
            
            # Create default products if JSON doesn't exist
            if not os.path.exists(json_file):
                print("📝 Creating default products...")
                create_default_products(json_file)
            
            # Load from JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                loaded_products = json.load(f)
            
            # Update global products
            products.clear()
            products.update(loaded_products)
            
            _last_update_time = current_time
            print(f"✅ SUCCESS: Loaded {len(products)} products from JSON")
            
            return True
                
        except Exception as e:
            print(f"❌ ERROR loading products: {e}")
            # Create fresh products if loading fails
            if not os.path.exists(json_file):
                create_default_products(json_file)
                with open(json_file, 'r', encoding='utf-8') as f:
                    products.update(json.load(f))
                print(f"✅ Recovered with {len(products)} default products")
                _last_update_time = current_time
                return True
            return False

def save_products():
    """Save products to JSON file - MAIN SAVE FUNCTION"""
    global products, _last_update_time
    
    print("💾 Saving products to JSON file...")
    
    json_file = get_products_file_path()
    
    with products_lock:
        try:
            # Create database directory if it doesn't exist
            database_dir = os.path.dirname(json_file)
            if not os.path.exists(database_dir):
                os.makedirs(database_dir)
                print(f"✅ Created database directory: {database_dir}")
            
            # Create a deep copy to avoid modification during save
            products_to_save = {}
            for product_id, product in products.items():
                products_to_save[product_id] = product.copy()
            
            # Save to JSON file with proper formatting
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(products_to_save, f, indent=2, ensure_ascii=False)
            
            _last_update_time = time.time()
            print(f"✅ SUCCESS: Saved {len(products_to_save)} products to JSON")
            
            # Force reload after save to ensure consistency
            load_products(force=True)
            
            return True
                
        except Exception as e:
            print(f"❌❌❌ CRITICAL ERROR in save_products: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def reload_products():
    """Reload products from JSON file - Use this to get latest data from file"""
    return load_products(force=True)

def create_default_products(json_file):
    """Create default products if no data exists"""
    print("🆕 Creating default products...")
    
    default_products = {
        "1": {
            "id": 1,
            "name": "Vitamin C Serum",
            "brand": "Garnier",
            "category": "Skincare",
            "stock": 265,
            "cost": 1000.0,
            "price": 2000.0,
            "country": "France",
            "description": "Brightening vitamin C serum for radiant skin",
            "created_date": datetime.now().strftime('%Y-%m-%d'),
            "is_active": True
        },
        "2": {
            "id": 2,
            "name": "Skin Cleanser", 
            "brand": "Cetaphil",
            "category": "Skincare",
            "stock": 272,
            "cost": 280.0,
            "price": 560.0,
            "country": "Switzerland",
            "description": "Gentle daily face cleanser for all skin types",
            "created_date": datetime.now().strftime('%Y-%m-%d'),
            "is_active": True
        },
        "3": {
            "id": 3,
            "name": "Sunscreen",
            "brand": "Aqualogica", 
            "category": "Skincare",
            "stock": 265,
            "cost": 700.0,
            "price": 1400.0,
            "country": "India",
            "description": "Hydrating sunscreen with SPF protection",
            "created_date": datetime.now().strftime('%Y-%m-%d'),
            "is_active": True
        },
        "4": {
            "id": 4,
            "name": "Moisturizing Cream",
            "brand": "Neutrogena",
            "category": "Skincare", 
            "stock": 150,
            "cost": 450.0,
            "price": 900.0,
            "country": "USA",
            "description": "Hydrating cream for dry skin",
            "created_date": datetime.now().strftime('%Y-%m-%d'),
            "is_active": True
        },
        "5": {
            "id": 5,
            "name": "Face Mask",
            "brand": "L'Oreal",
            "category": "Skincare",
            "stock": 180, 
            "cost": 300.0,
            "price": 600.0,
            "country": "France",
            "description": "Clay face mask for deep cleansing",
            "created_date": datetime.now().strftime('%Y-%m-%d'),
            "is_active": True
        }
    }
    
    # Ensure database directory exists
    database_dir = os.path.dirname(json_file)
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)
        print(f"✅ Created database directory: {database_dir}")
    
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(default_products, f, indent=2, ensure_ascii=False)
        print(f"✅ Created default products with {len(default_products)} items")
        return True
    except Exception as e:
        print(f"❌ Error creating default products: {e}")
        return False

def get_next_product_id():
    """Get next available product ID"""
    if not products:
        return 1
    
    max_id = 0
    for product_id in products.keys():
        try:
            pid = int(product_id)
            if pid > max_id:
                max_id = pid
        except ValueError:
            continue
    
    return max_id + 1

def add_product(product_data):
    """Add new product to inventory"""
    print(f"🆕 Adding new product: {product_data['name']}")
    
    try:
        # Ensure we have latest data
        load_products(force=True)
        
        product_id = get_next_product_id()
        
        products[str(product_id)] = {
            'id': product_id,
            'name': product_data['name'],
            'brand': product_data['brand'],
            'category': product_data.get('category', 'Skincare'),
            'stock': product_data['stock'],
            'cost': product_data['cost'],
            'price': product_data['cost'] * 2,  # Auto-calculate selling price
            'country': product_data.get('country', ''),
            'description': product_data.get('description', ''),
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'is_active': True
        }
        
        # Save immediately to persist the new product
        if save_products():
            print(f"✅ Product '{product_data['name']}' added successfully with ID {product_id}")
            return {'success': True, 'product_id': product_id}
        else:
            print(f"❌ Failed to save new product '{product_data['name']}'")
            # Remove from memory if save failed
            if str(product_id) in products:
                del products[str(product_id)]
            return {'success': False, 'error': 'Failed to save products to database'}
        
    except Exception as e:
        print(f"❌ Error adding product: {e}")
        return {'success': False, 'error': str(e)}

def update_product(product_id, product_data):
    """Update existing product"""
    print(f"✏️ Updating product ID {product_id}")
    
    try:
        # Ensure we have latest data
        load_products(force=True)
        
        product_id_str = str(product_id)
        if product_id_str not in products:
            print(f"❌ Product ID {product_id} not found")
            return {'success': False, 'error': 'Product not found'}
        
        # Update product fields
        product = products[product_id_str]
        old_name = product['name']
        
        for key, value in product_data.items():
            if key in product:
                product[key] = value
        
        # Auto-update price if cost changed
        if 'cost' in product_data:
            product['price'] = product_data['cost'] * 2
        
        # Save immediately to persist changes
        if save_products():
            print(f"✅ Product '{old_name}' updated successfully")
            return {'success': True}
        else:
            print(f"❌ Failed to save updated product '{old_name}'")
            # Reload from file to undo memory changes if save failed
            load_products(force=True)
            return {'success': False, 'error': 'Failed to save products to database'}
        
    except Exception as e:
        print(f"❌ Error updating product: {e}")
        return {'success': False, 'error': str(e)}

def delete_product(product_id):
    """Soft delete product (set inactive)"""
    print(f"🗑️ Soft deleting product ID {product_id}")
    
    try:
        # Ensure we have latest data
        load_products(force=True)
        
        product_id_str = str(product_id)
        if product_id_str not in products:
            print(f"❌ Product ID {product_id} not found")
            return {'success': False, 'error': 'Product not found'}
        
        product_name = products[product_id_str]['name']
        products[product_id_str]['is_active'] = False
        
        # Save immediately to persist deletion
        if save_products():
            print(f"✅ Product '{product_name}' soft deleted successfully")
            return {'success': True}
        else:
            print(f"❌ Failed to save deleted product '{product_name}'")
            # Reload from file to undo memory changes if save failed
            load_products(force=True)
            return {'success': False, 'error': 'Failed to save products to database'}
        
    except Exception as e:
        print(f"❌ Error deleting product: {e}")
        return {'success': False, 'error': str(e)}

def update_product_stock(product_id, quantity_change):
    """Update product stock (for purchases and restocks) - FIXED: Better synchronization"""
    print(f"📦 Updating stock for product ID {product_id}: {quantity_change}")
    
    try:
        # CRITICAL: Always reload products first to get latest data
        if not load_products(force=True):
            return {'success': False, 'error': 'Failed to load products'}
        
        product_id_str = str(product_id)
        
        if product_id_str not in products:
            print(f"❌ Product ID {product_id} not found for stock update")
            return {'success': False, 'error': 'Product not found'}
        
        product = products[product_id_str]
        old_stock = product['stock']
        new_stock = old_stock + quantity_change
        
        if new_stock < 0:
            print(f"❌ Insufficient stock: {old_stock} available, tried to remove {abs(quantity_change)}")
            return {'success': False, 'error': f'Insufficient stock. Available: {old_stock}'}
        
        product['stock'] = new_stock
        print(f"✅ Stock updated: {product['name']} {old_stock} → {new_stock}")
        
        # Save immediately to persist stock change
        if save_products():
            print(f"✅ Stock change saved for '{product['name']}'")
            return {'success': True, 'old_stock': old_stock, 'new_stock': new_stock}
        else:
            print(f"❌ Failed to save stock update for '{product['name']}'")
            # Revert memory change if save failed
            product['stock'] = old_stock
            return {'success': False, 'error': 'Failed to save stock update'}
        
    except Exception as e:
        print(f"❌ Error updating product stock: {e}")
        return {'success': False, 'error': str(e)}

def get_product(product_id):
    """Get single product by ID"""
    # Always load fresh data
    load_products()
    product_id_str = str(product_id)
    return products.get(product_id_str)

def get_all_products(active_only=True):
    """Get all products, optionally only active ones"""
    # Always load fresh data
    load_products()
    if active_only:
        return {pid: p for pid, p in products.items() if p.get('is_active', True)}
    return products

def get_products_by_category(category):
    """Get products by category"""
    load_products()
    return {pid: p for pid, p in products.items() 
            if p.get('category') == category and p.get('is_active', True)}

def get_low_stock_products(threshold=10):
    """Get products with low stock"""
    load_products()
    return {pid: p for pid, p in products.items() 
            if p.get('stock', 0) <= threshold and p.get('is_active', True)}

# Initialize products when module is imported
print("🚀 Initializing products module...")
load_products(force=True)