'''
Admin database operations for WeCare Beauty Store
Handles admin authentication, authorization, and wallet management
'''

import json
import os
from datetime import datetime
import hashlib
from collections import defaultdict

# Get absolute paths for database files
def get_db_path(filename):
    """Get absolute path to database file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return os.path.join(parent_dir, 'database', filename)

# Database folder and files with absolute paths
ADMIN_DB = get_db_path('admins.json')
ADMIN_WALLET_DB = get_db_path('admin_wallet.json')
TRANSACTION_DB = get_db_path('transactions.json')
SALES_DB = get_db_path('sales.json')

def init_admin_database():
    '''Initialize admin database with default admin'''
    # Create database folder if it doesn't exist
    db_folder = os.path.dirname(ADMIN_DB)
    if not os.path.exists(db_folder):
        os.makedirs(db_folder)
    
    # Initialize admins.json with default admin
    if not os.path.exists(ADMIN_DB):
        default_admin = {
            '1': {
                'admin_id': 1,
                'username': 'admin',
                'password': hash_password('admin123'),  # Default password
                'email': 'admin@wecarebeauty.com',
                'full_name': 'System Administrator',
                'role': 'super_admin',
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'last_login': None,
                'is_active': True
            }
        }
        
        with open(ADMIN_DB, 'w') as f:
            json.dump(default_admin, f, indent=2)

def init_admin_wallet():
    '''Initialize admin wallet with default balance'''
    if not os.path.exists(ADMIN_WALLET_DB):
        default_wallet = {
            'balance': 50000.0,
            'total_revenue': 0.0,
            'total_transactions': 0,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(ADMIN_WALLET_DB, 'w') as f:
            json.dump(default_wallet, f, indent=2)

def init_transaction_db():
    '''Initialize transactions database'''
    if not os.path.exists(TRANSACTION_DB):
        with open(TRANSACTION_DB, 'w') as f:
            json.dump([], f)

def init_sales_db():
    '''Initialize sales database'''
    if not os.path.exists(SALES_DB):
        with open(SALES_DB, 'w') as f:
            json.dump([], f)

def hash_password(password):
    '''Hash password for security'''
    return hashlib.sha256(password.encode()).hexdigest()

def get_next_admin_id():
    '''Get next available admin ID'''
    try:
        with open(ADMIN_DB, 'r') as f:
            admins = json.load(f)
        
        if not admins:
            return 1
        
        max_id = max(int(aid) for aid in admins.keys())
        return max_id + 1
    except:
        return 1

def authenticate_admin(username, password):
    '''Authenticate admin login'''
    init_admin_database()
    
    try:
        with open(ADMIN_DB, 'r') as f:
            admins = json.load(f)
        
        hashed_password = hash_password(password)
        
        for admin_id, admin in admins.items():
            if (admin['username'] == username and 
                admin['password'] == hashed_password and
                admin['is_active']):
                
                # Update last login
                admin['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                admins[admin_id] = admin
                
                with open(ADMIN_DB, 'w') as f:
                    json.dump(admins, f, indent=2)
                
                return {'success': True, 'admin': admin}
        
        return {'success': False, 'error': 'Invalid username or password'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_admin(admin_id):
    '''Get admin by ID'''
    init_admin_database()
    
    try:
        with open(ADMIN_DB, 'r') as f:
            admins = json.load(f)
        
        admin = admins.get(str(admin_id))
        if admin:
            # Remove password from returned data
            admin_data = admin.copy()
            admin_data.pop('password', None)
            return admin_data
        return None
    
    except:
        return None

def create_admin(username, password, email, full_name, role='admin'):
    '''Create a new admin account'''
    init_admin_database()
    
    try:
        with open(ADMIN_DB, 'r') as f:
            admins = json.load(f)
        
        # Check if username already exists
        for admin_id, admin in admins.items():
            if admin['username'] == username:
                return {'success': False, 'error': 'Username already exists'}
        
        # Create new admin
        admin_id = get_next_admin_id()
        
        admins[str(admin_id)] = {
            'admin_id': admin_id,
            'username': username,
            'password': hash_password(password),
            'email': email,
            'full_name': full_name,
            'role': role,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'last_login': None,
            'is_active': True
        }
        
        with open(ADMIN_DB, 'w') as f:
            json.dump(admins, f, indent=2)
        
        return {'success': True, 'admin_id': admin_id}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_all_admins():
    '''Get all admins (for super admin view)'''
    init_admin_database()
    
    try:
        with open(ADMIN_DB, 'r') as f:
            admins = json.load(f)
        
        # Remove passwords from returned data
        admins_data = {}
        for admin_id, admin in admins.items():
            admin_data = admin.copy()
            admin_data.pop('password', None)
            admins_data[admin_id] = admin_data
        
        return admins_data
    
    except:
        return {}

# ==================== ADMIN WALLET FUNCTIONS ====================

def get_admin_wallet():
    '''Get admin wallet information'''
    init_admin_wallet()
    
    try:
        with open(ADMIN_WALLET_DB, 'r') as f:
            wallet = json.load(f)
        return wallet
    except:
        return {'balance': 50000.0, 'total_revenue': 0.0, 'total_transactions': 0}

def update_admin_wallet(amount, transaction_type='revenue'):
    '''Update admin wallet balance'''
    init_admin_wallet()
    
    try:
        with open(ADMIN_WALLET_DB, 'r') as f:
            wallet = json.load(f)
        
        if transaction_type == 'revenue':
            wallet['balance'] += amount
            wallet['total_revenue'] += amount
        elif transaction_type == 'expense':
            wallet['balance'] -= amount
        
        wallet['total_transactions'] += 1
        wallet['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(ADMIN_WALLET_DB, 'w') as f:
            json.dump(wallet, f, indent=2)
        
        return wallet
    except Exception as e:
        print(f"Error updating admin wallet: {e}")
        return None

def add_revenue_to_admin(amount):
    '''Add revenue to admin wallet from customer purchases'''
    return update_admin_wallet(amount, 'revenue')

def deduct_admin_balance(amount):
    '''Deduct from admin wallet (for restocking, etc.)'''
    return update_admin_wallet(amount, 'expense')

def get_admin_balance():
    '''Get current admin wallet balance'''
    wallet = get_admin_wallet()
    return wallet.get('balance', 0)

# ==================== SALES TRACKING FUNCTIONS ====================

def log_sale(customer_id, product_id, product_name, quantity, unit_price, total_price, timestamp=None):
    '''Log a sale transaction'''
    init_sales_db()
    
    try:
        with open(SALES_DB, 'r') as f:
            sales = json.load(f)
        
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sale_record = {
            'sale_id': len(sales) + 1,
            'customer_id': customer_id,
            'product_id': product_id,
            'product_name': product_name,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': total_price,
            'timestamp': timestamp
        }
        
        sales.append(sale_record)
        
        with open(SALES_DB, 'w') as f:
            json.dump(sales, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error logging sale: {e}")
        return False

def get_all_sales():
    '''Get all sales records'''
    init_sales_db()
    
    try:
        with open(SALES_DB, 'r') as f:
            sales = json.load(f)
        return sales
    except:
        return []

def get_sales_by_date_range(start_date=None, end_date=None):
    '''Get sales within a date range'''
    sales = get_all_sales()
    
    if not start_date and not end_date:
        return sales
    
    filtered_sales = []
    for sale in sales:
        sale_date = sale['timestamp'].split(' ')[0]  # Extract date part
        
        if start_date and sale_date < start_date:
            continue
        if end_date and sale_date > end_date:
            continue
            
        filtered_sales.append(sale)
    
    return filtered_sales

# ==================== TRANSACTION LOGGING FUNCTIONS ====================

def log_transaction(customer_id, amount, transaction_type, description):
    '''Log financial transactions'''
    init_transaction_db()
    
    try:
        with open(TRANSACTION_DB, 'r') as f:
            transactions = json.load(f)
        
        transaction = {
            'id': len(transactions) + 1,
            'customer_id': customer_id,
            'amount': amount,
            'type': transaction_type,
            'description': description,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        transactions.append(transaction)
        
        with open(TRANSACTION_DB, 'w') as f:
            json.dump(transactions, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error logging transaction: {e}")
        return False

def get_all_transactions():
    '''Get all transactions'''
    init_transaction_db()
    
    try:
        with open(TRANSACTION_DB, 'r') as f:
            transactions = json.load(f)
        return transactions
    except:
        return []

def get_transactions_by_customer(customer_id):
    '''Get transactions for a specific customer'''
    transactions = get_all_transactions()
    return [t for t in transactions if t.get('customer_id') == customer_id]

def get_recent_transactions(limit=10):
    '''Get recent transactions'''
    transactions = get_all_transactions()
    return sorted(transactions, key=lambda x: x['timestamp'], reverse=True)[:limit]

# ==================== SALES ANALYTICS FUNCTIONS ====================

def get_sales_analytics():
    '''Get comprehensive sales analytics'''
    try:
        from .customer_ops import get_all_customers
        from .read_ops import products
        
        customers = get_all_customers()
        sales = get_all_sales()
        transactions = get_all_transactions()
        
        # Calculate actual revenue from sales
        total_revenue = sum(sale['total_price'] for sale in sales)
        
        # Customer metrics
        total_customers = len(customers)
        customers_with_purchases = set(sale['customer_id'] for sale in sales)
        active_customers = len(customers_with_purchases)
        total_products = len(products)
        
        # Customer segmentation
        customers_with_wallet = len([c for c in customers.values() if c.get('wallet')])
        customers_without_wallet = total_customers - customers_with_wallet
        
        # Transaction metrics
        revenue_transactions = [t for t in transactions if t.get('type') == 'revenue']
        total_transactions_count = len(revenue_transactions)
        
        # Sales metrics
        total_orders = len(sales)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        analytics = {
            'total_revenue': total_revenue,
            'total_customers': total_customers,
            'active_customers': active_customers,
            'total_products': total_products,
            'customers_with_wallet': customers_with_wallet,
            'customers_without_wallet': customers_without_wallet,
            'total_transactions': total_transactions_count,
            'total_orders': total_orders,
            'average_order_value': average_order_value,
            'conversion_rate': (active_customers / total_customers * 100) if total_customers > 0 else 0
        }
        
        return analytics
        
    except Exception as e:
        print(f"Error generating sales analytics: {e}")
        return {
            'total_revenue': 0,
            'total_customers': 0,
            'active_customers': 0,
            'total_products': 0,
            'customers_with_wallet': 0,
            'customers_without_wallet': 0,
            'total_transactions': 0,
            'total_orders': 0,
            'average_order_value': 0,
            'conversion_rate': 0
        }

def get_daily_sales():
    '''Get daily sales data'''
    sales = get_all_sales()
    
    # Group sales by date
    daily_sales = defaultdict(lambda: {'revenue': 0, 'orders': 0})
    
    for sale in sales:
        date = sale['timestamp'].split(' ')[0]  # Extract date part
        daily_sales[date]['revenue'] += sale['total_price']
        daily_sales[date]['orders'] += 1
    
    # Convert to list and sort by date
    result = [{'date': date, 'revenue': data['revenue'], 'orders': data['orders']} 
              for date, data in daily_sales.items()]
    
    return sorted(result, key=lambda x: x['date'], reverse=True)[:7]  # Last 7 days

def get_top_products():
    '''Get top selling products based on actual sales data'''
    sales = get_all_sales()
    
    # Aggregate product sales
    product_sales = defaultdict(lambda: {'quantity': 0, 'revenue': 0})
    
    for sale in sales:
        product_id = sale['product_id']
        product_sales[product_id]['quantity'] += sale['quantity']
        product_sales[product_id]['revenue'] += sale['total_price']
        product_sales[product_id]['name'] = sale['product_name']
    
    # Get product details and combine with sales data
    from .read_ops import products
    
    top_products = []
    for product_id, sales_data in product_sales.items():
        product_info = products.get(int(product_id), {})
        top_products.append({
            'id': product_id,
            'name': sales_data.get('name', product_info.get('name', 'Unknown')),
            'brand': product_info.get('brand', 'Unknown'),
            'sales': sales_data['quantity'],
            'revenue': sales_data['revenue'],
            'stock': product_info.get('stock', 0)
        })
    
    # Sort by revenue (most profitable first)
    return sorted(top_products, key=lambda x: x['revenue'], reverse=True)[:5]

def get_customer_insights():
    '''Get customer behavior insights based on actual sales data'''
    from .customer_ops import get_all_customers

    customers = get_all_customers()
    sales = get_all_sales()
    
    if not customers:
        return {
            'total_customers': 0,
            'avg_spent_per_customer': 0,
            'avg_orders_per_customer': 0,
            'top_spender': {'name': 'No purchases yet', 'total_spent': 0},
            'most_frequent_buyer': {'name': 'No purchases yet', 'purchase_count': 0}
        }
    
    # Calculate customer spending from actual sales
    customer_spending = defaultdict(lambda: {'total_spent': 0, 'order_count': 0, 'name': ''})
    
    for sale in sales:
        customer_id = sale['customer_id']
        customer_spending[customer_id]['total_spent'] += sale['total_price']
        customer_spending[customer_id]['order_count'] += 1
        
        # Get customer name if not set
        if not customer_spending[customer_id]['name']:
            customer = customers.get(str(customer_id), {})
            customer_spending[customer_id]['name'] = customer.get('name', 'Unknown Customer')
    
    # If no sales data, return default values
    if not customer_spending:
        return {
            'total_customers': len(customers),
            'avg_spent_per_customer': 0,
            'avg_orders_per_customer': 0,
            'top_spender': {'name': 'No purchases yet', 'total_spent': 0},
            'most_frequent_buyer': {'name': 'No purchases yet', 'purchase_count': 0}
        }
    
    # Calculate averages only for customers who made purchases
    customers_with_purchases = [data for data in customer_spending.values() if data['order_count'] > 0]
    
    if customers_with_purchases:
        total_spent = sum(data['total_spent'] for data in customers_with_purchases)
        total_orders = sum(data['order_count'] for data in customers_with_purchases)
        
        avg_spent = total_spent / len(customers_with_purchases) if customers_with_purchases else 0
        avg_orders = total_orders / len(customers_with_purchases) if customers_with_purchases else 0
    else:
        avg_spent = 0
        avg_orders = 0
    
    # Find top performers from customers who actually made purchases
    if customer_spending:
        # Filter out customers with no purchases
        active_customers = {cid: data for cid, data in customer_spending.items() if data['order_count'] > 0}
        
        if active_customers:
            top_spender_id = max(active_customers.keys(), 
                               key=lambda x: active_customers[x]['total_spent'])
            most_frequent_id = max(active_customers.keys(), 
                                 key=lambda x: active_customers[x]['order_count'])
            
            top_spender = {
                'name': active_customers[top_spender_id]['name'],
                'total_spent': active_customers[top_spender_id]['total_spent']
            }
            most_frequent_buyer = {
                'name': active_customers[most_frequent_id]['name'],
                'purchase_count': active_customers[most_frequent_id]['order_count']
            }
        else:
            top_spender = {'name': 'No purchases yet', 'total_spent': 0}
            most_frequent_buyer = {'name': 'No purchases yet', 'purchase_count': 0}
    else:
        top_spender = {'name': 'No purchases yet', 'total_spent': 0}
        most_frequent_buyer = {'name': 'No purchases yet', 'purchase_count': 0}
    
    insights = {
        'total_customers': len(customers),
        'avg_spent_per_customer': avg_spent,
        'avg_orders_per_customer': avg_orders,
        'top_spender': top_spender,
        'most_frequent_buyer': most_frequent_buyer
    }
    
    return insights