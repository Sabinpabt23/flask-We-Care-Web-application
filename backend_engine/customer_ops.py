import json
import os
from datetime import datetime
import hashlib

# Get absolute paths for database files
def get_db_path(filename):
    """Get absolute path to database file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return os.path.join(parent_dir, 'database', filename)

# Database files with absolute paths
CUSTOMER_DB = get_db_path('customers.json')
WALLET_DB = get_db_path('wallets.json')
TRANSACTION_DB = get_db_path('customer_transactions.json')

def init_database():
    '''Initialize database folder and files'''
    # Create database folder if it doesn't exist
    db_folder = os.path.dirname(CUSTOMER_DB)
    if not os.path.exists(db_folder):
        os.makedirs(db_folder)
        print(f"✅ Created database folder: {db_folder}")
    
    # Initialize customers.json
    if not os.path.exists(CUSTOMER_DB):
        with open(CUSTOMER_DB, 'w') as f:
            json.dump({}, f)
        print(f"✅ Created customers database: {CUSTOMER_DB}")
    
    # Initialize wallets.json
    if not os.path.exists(WALLET_DB):
        with open(WALLET_DB, 'w') as f:
            json.dump({}, f)
        print(f"✅ Created wallets database: {WALLET_DB}")

def hash_password(password):
    '''Hash password for security'''
    return hashlib.sha256(password.encode()).hexdigest()

def get_next_customer_id():
    '''Get next available customer ID'''
    try:
        with open(CUSTOMER_DB, 'r') as f:
            customers = json.load(f)
        
        if not customers:
            return 1
        
        max_id = max(int(cid) for cid in customers.keys())
        return max_id + 1
    except:
        return 1

def register_customer(name, email, phone, password, setup_wallet=False, wallet_data=None):
    '''Register a new customer'''
    init_database()
    
    try:
        with open(CUSTOMER_DB, 'r') as f:
            customers = json.load(f)
        
        # Check if email already exists
        for customer_id, customer in customers.items():
            if customer['email'].lower() == email.lower():
                return {'success': False, 'error': 'Email already registered'}
        
        # Create new customer
        customer_id = get_next_customer_id()
        join_date = datetime.now().strftime('%Y-%m-%d')
        
        customers[str(customer_id)] = {
            'customer_id': customer_id,
            'name': name,
            'email': email.lower(),
            'phone': phone,
            'password': hash_password(password),
            'join_date': join_date,
            'total_spent': 0,
            'purchase_count': 0,
            'points': 0,
            'last_purchase': None,
            'wallet_setup': setup_wallet
        }
        
        with open(CUSTOMER_DB, 'w') as f:
            json.dump(customers, f, indent=2)
        
        # Setup wallet if requested
        if setup_wallet and wallet_data:
            setup_customer_wallet(customer_id, wallet_data)
        
        return {'success': True, 'customer_id': customer_id}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def setup_customer_wallet(customer_id, wallet_data):
    '''Setup customer wallet with card details'''
    try:
        with open(WALLET_DB, 'r') as f:
            wallets = json.load(f)
        
        wallets[str(customer_id)] = {
            'customer_id': customer_id,
            'card_type': wallet_data['card_type'],
            'card_number': wallet_data['card_number'][-4:],  # Store only last 4 digits
            'card_holder': wallet_data['card_holder'],
            'expiry_date': wallet_data['expiry_date'],
            'cvv_hash': hashlib.sha256(wallet_data.get('cvv', '').encode()).hexdigest(),  # Hash CVV
            'balance': 10000.0,
            'setup_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        with open(WALLET_DB, 'w') as f:
            json.dump(wallets, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error setting up wallet: {e}")
        return False

def get_customer_wallet(customer_id):
    '''Get customer wallet details'''
    try:
        with open(WALLET_DB, 'r') as f:
            wallets = json.load(f)
        
        return wallets.get(str(customer_id))
    except:
        return None

def get_wallet_balance(customer_id):
    '''Get customer wallet balance'''
    wallet = get_customer_wallet(customer_id)
    if wallet:
        return wallet.get('balance', 0)
    return 0

def update_wallet_balance(customer_id, amount):
    """Update customer wallet balance and log transaction"""
    try:
        with open(WALLET_DB, 'r') as f:
            wallets = json.load(f)
        
        wallet = wallets.get(str(customer_id))
        if wallet:
            old_balance = wallet['balance']
            wallet['balance'] += amount
            new_balance = wallet['balance']
            wallets[str(customer_id)] = wallet
            
            with open(WALLET_DB, 'w') as f:
                json.dump(wallets, f, indent=2)
            
            # Log the transaction
            if amount > 0:
                transaction_type = 'add'
                description = f"Money added to wallet"
            else:
                transaction_type = 'withdraw' 
                description = f"Money withdrawn from wallet"
            
            log_customer_transaction(
                customer_id, 
                transaction_type, 
                abs(amount), 
                description,
                new_balance
            )
            
            return new_balance
        return None
    except Exception as e:
        print(f"Error updating wallet: {e}")
        return None

def login_customer(email, password):
    '''Customer login verification'''
    init_database()
    
    try:
        with open(CUSTOMER_DB, 'r') as f:
            customers = json.load(f)
        
        hashed_password = hash_password(password)
        
        for customer_id, customer in customers.items():
            if (customer['email'].lower() == email.lower() and 
                customer['password'] == hashed_password):
                return {'success': True, 'customer': customer}
        
        return {'success': False, 'error': 'Invalid email or password'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ==================== LOYALTY SYSTEM FUNCTIONS ====================

def get_loyalty_tier(points):
    '''Calculate loyalty tier based on points'''
    if points >= 2000:
        return 'diamond'
    elif points >= 1000:
        return 'gold'
    elif points >= 500:
        return 'silver'
    elif points >= 100:
        return 'bronze'
    else:
        return 'none'

def get_loyalty_tier_info(points):
    '''Get detailed loyalty tier information'''
    current_tier = get_loyalty_tier(points)
    
    # Define tier thresholds and next tier info
    tier_info = {
        'none': {
            'name': 'No Tier',
            'next_tier': 'bronze',
            'points_needed': 100,
            'min_points': 0,
            'max_points': 99
        },
        'bronze': {
            'name': 'Bronze Member',
            'next_tier': 'silver',
            'points_needed': 500 - points,
            'min_points': 100,
            'max_points': 499
        },
        'silver': {
            'name': 'Silver Member',
            'next_tier': 'gold',
            'points_needed': 1000 - points,
            'min_points': 500,
            'max_points': 999
        },
        'gold': {
            'name': 'Gold Member',
            'next_tier': 'diamond',
            'points_needed': 2000 - points,
            'min_points': 1000,
            'max_points': 1999
        },
        'diamond': {
            'name': 'Diamond Member',
            'next_tier': None,
            'points_needed': 0,
            'min_points': 2000,
            'max_points': float('inf')
        }
    }
    
    return tier_info[current_tier]

def get_customer(customer_id):
    '''Get customer by ID'''
    init_database()
    
    try:
        with open(CUSTOMER_DB, 'r') as f:
            customers = json.load(f)
        
        customer = customers.get(str(customer_id))
        if customer:
            # Remove password from returned data
            customer_data = customer.copy()
            customer_data.pop('password', None)
            
            # Add wallet info
            wallet = get_customer_wallet(customer_id)
            customer_data['wallet'] = wallet
            customer_data['wallet_balance'] = get_wallet_balance(customer_id)
            
            # Add loyalty tier information
            points = customer_data.get('points', 0)
            customer_data['loyalty_tier'] = get_loyalty_tier(points)
            customer_data['loyalty_info'] = get_loyalty_tier_info(points)
            
            return customer_data
        return None
    
    except:
        return None

def update_customer_purchase(customer_id, amount):
    '''Update customer after a purchase'''
    init_database()
    
    try:
        with open(CUSTOMER_DB, 'r') as f:
            customers = json.load(f)
        
        customer = customers.get(str(customer_id))
        if customer:
            customer['total_spent'] += amount
            customer['purchase_count'] += 1
            customer['last_purchase'] = datetime.now().strftime('%Y-%m-%d')
            
            # Add points (1 point per ₹100 spent)
            points_earned = amount // 100
            customer['points'] += points_earned
            
            with open(CUSTOMER_DB, 'w') as f:
                json.dump(customers, f, indent=2)
            
            return {'success': True, 'points_earned': points_earned}
        
        return {'success': False, 'error': 'Customer not found'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def verify_customer_identity(customer_id, name, email, phone):
    '''Verify customer identity during purchase'''
    try:
        with open(CUSTOMER_DB, 'r') as f:
            customers = json.load(f)
        
        customer = customers.get(str(customer_id))
        if not customer:
            return {'success': False, 'error': 'Customer not found'}
        
        # Verify identity information
        if (customer['name'].lower() != name.lower() or 
            customer['email'].lower() != email.lower() or 
            customer['phone'] != phone):
            return {'success': False, 'error': 'Identity verification failed. Please check your information.'}
        
        return {'success': True, 'customer': customer}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def verify_card_information(customer_id, card_holder, card_last_four):
    '''Verify card information during purchase'''
    try:
        with open(WALLET_DB, 'r') as f:
            wallets = json.load(f)
        
        wallet = wallets.get(str(customer_id))
        if not wallet:
            return {'success': False, 'error': 'Wallet not found'}
        
        # Verify card information
        if (wallet['card_holder'].lower() != card_holder.lower() or 
            wallet['card_number'] != card_last_four):
            return {'success': False, 'error': 'Card verification failed. Please check your card details.'}
        
        return {'success': True, 'wallet': wallet}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def delete_customer_account(customer_id, confirm_password):
    '''Delete customer account and all associated data'''
    try:
        with open(CUSTOMER_DB, 'r') as f:
            customers = json.load(f)
        
        customer = customers.get(str(customer_id))
        if not customer:
            return {'success': False, 'error': 'Customer not found'}
        
        # Verify password before deletion
        hashed_password = hash_password(confirm_password)
        if customer['password'] != hashed_password:
            return {'success': False, 'error': 'Incorrect password. Account deletion failed.'}
        
        # Get wallet balance for refund message
        wallet_balance = get_wallet_balance(customer_id)
        
        # Remove customer from database
        del customers[str(customer_id)]
        
        with open(CUSTOMER_DB, 'w') as f:
            json.dump(customers, f, indent=2)
        
        # Remove wallet data if exists
        remove_customer_wallet(customer_id)
        
        return {
            'success': True, 
            'message': f'Account deleted successfully. Wallet balance ₹{wallet_balance} has been forfeited.',
            'wallet_balance': wallet_balance
        }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def remove_customer_wallet(customer_id):
    '''Remove customer wallet data'''
    try:
        with open(WALLET_DB, 'r') as f:
            wallets = json.load(f)
        
        if str(customer_id) in wallets:
            del wallets[str(customer_id)]
            
            with open(WALLET_DB, 'w') as f:
                json.dump(wallets, f, indent=2)
        
        return True
    except:
        return False

def get_all_customers():
    '''Get all customers (for admin view)'''
    init_database()
    
    try:
        with open(CUSTOMER_DB, 'r') as f:
            customers = json.load(f)
        
        # Remove passwords from returned data
        customers_data = {}
        for customer_id, customer in customers.items():
            customer_data = customer.copy()
            customer_data.pop('password', None)
            
            # Add wallet info
            wallet = get_customer_wallet(customer_id)
            customer_data['wallet'] = wallet
            customer_data['wallet_balance'] = get_wallet_balance(customer_id)
            
            # Add loyalty tier information
            points = customer_data.get('points', 0)
            customer_data['loyalty_tier'] = get_loyalty_tier(points)
            customer_data['loyalty_info'] = get_loyalty_tier_info(points)
            
            customers_data[customer_id] = customer_data
        
        return customers_data
    
    except:
        return {}
    
# ==================== PURCHASE HISTORY FUNCTIONS ====================

def get_customer_purchase_history(customer_id):
    '''Get customer's detailed purchase history'''
    # This is a placeholder - will be enhanced with actual order tracking
    try:
        # For now, return basic info from customer data
        customer = get_customer(customer_id)
        if not customer:
            return []
        
        # Placeholder purchase history
        purchase_history = []
        if customer.get('purchase_count', 0) > 0:
            purchase_history.append({
                'order_id': f"ORD{customer_id}001",
                'date': customer.get('last_purchase', '2025-11-20'),
                'total_amount': customer.get('total_spent', 0),
                'items_count': customer.get('purchase_count', 0),
                'status': 'completed',
                'items': [
                    {
                        'name': 'Beauty Products Bundle',
                        'quantity': customer.get('purchase_count', 1),
                        'price': customer.get('total_spent', 0)
                    }
                ]
            })
        
        return purchase_history
        
    except Exception as e:
        print(f"Error getting purchase history: {e}")
        return []

def init_order_history():
    '''Initialize order history database'''
    ORDER_DB = get_db_path('orders.json')  # Use the same path function
    if not os.path.exists(ORDER_DB):
        # Create database folder if it doesn't exist
        db_folder = os.path.dirname(ORDER_DB)
        if not os.path.exists(db_folder):
            os.makedirs(db_folder)
        
        with open(ORDER_DB, 'w') as f:
            json.dump({}, f)
        print(f"✅ Created orders database: {ORDER_DB}")

def save_order_to_history(customer_id, order_data):
    '''Save order to purchase history (placeholder)'''
    # This will be implemented when we add proper order tracking
    print(f"Order saved for customer {customer_id}: {order_data}")
    return True

# ==================== TRANSACTION HISTORY FUNCTIONS ====================

def init_transaction_history():
    """Initialize transaction history database"""
    # Use the global TRANSACTION_DB path
    if not os.path.exists(TRANSACTION_DB):
        # Create database folder if it doesn't exist
        db_folder = os.path.dirname(TRANSACTION_DB)
        if not os.path.exists(db_folder):
            os.makedirs(db_folder)
        
        # Create an empty dictionary structure, not an empty list
        with open(TRANSACTION_DB, 'w') as f:
            json.dump({}, f, indent=2)
        print(f"✅ Created transaction database: {TRANSACTION_DB}")
    else:
        print(f"✅ Transaction database exists: {TRANSACTION_DB}")
        

def log_customer_transaction(customer_id, transaction_type, amount, description, balance_after):
    """Log a customer wallet transaction"""
    try:
        print(f"🔄 Attempting to log transaction for customer {customer_id}")
        print(f"   Type: {transaction_type}, Amount: {amount}, Desc: {description}")
        
        # Ensure database folder exists
        db_folder = os.path.dirname(TRANSACTION_DB)
        if not os.path.exists(db_folder):
            os.makedirs(db_folder)
            print(f"✅ Created database folder: {db_folder}")
        
        # Initialize file if it doesn't exist
        if not os.path.exists(TRANSACTION_DB):
            with open(TRANSACTION_DB, 'w') as f:
                json.dump({}, f, indent=2)
            print(f"✅ Created transaction file: {TRANSACTION_DB}")
        
        # Read existing transactions
        with open(TRANSACTION_DB, 'r') as f:
            try:
                transactions = json.load(f)
                print(f"✅ Loaded transactions: {len(transactions)} customers")
            except json.JSONDecodeError:
                print("⚠️  Transaction file corrupted, creating new one")
                transactions = {}
        
        # Initialize customer transaction list if not exists
        customer_id_str = str(customer_id)
        if customer_id_str not in transactions:
            transactions[customer_id_str] = []
            print(f"✅ Created transaction list for customer {customer_id}")
        
        # Create transaction record
        transaction = {
            'id': len(transactions[customer_id_str]) + 1,
            'type': transaction_type,
            'amount': float(amount),
            'description': description,
            'balance_after': float(balance_after),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Add transaction
        transactions[customer_id_str].append(transaction)
        print(f"✅ Added transaction: {transaction}")
        
        # Save back to file
        with open(TRANSACTION_DB, 'w') as f:
            json.dump(transactions, f, indent=2)
        
        print(f"✅ Transaction logged successfully for customer {customer_id}")
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR logging transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_customer_transactions(customer_id, limit=10):
    """Get customer transaction history"""
    try:
        # Check if file exists
        if not os.path.exists(TRANSACTION_DB):
            print(f"⚠️  Transaction file not found: {TRANSACTION_DB}")
            return []
        
        with open(TRANSACTION_DB, 'r') as f:
            try:
                transactions = json.load(f)
            except json.JSONDecodeError:
                print("⚠️  Could not read transaction file")
                return []
        
        customer_tx = transactions.get(str(customer_id), [])
        print(f"✅ Found {len(customer_tx)} transactions for customer {customer_id}")
        
        # Sort by timestamp (newest first) and limit results
        if customer_tx:
            customer_tx.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return customer_tx[:limit]
    except Exception as e:
        print(f"❌ Error getting transactions: {e}")
        return []
    
def get_transaction_stats(customer_id):
    """Get transaction statistics for a customer"""
    transactions = get_customer_transactions(customer_id, limit=100)  # Get more for stats
    
    stats = {
        'total_transactions': len(transactions),
        'total_added': 0,
        'total_spent': 0,
        'last_transaction': None,
        'transaction_count_30d': 0
    }
    
    # Calculate 30 days ago
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    for tx in transactions:
        if tx['type'] == 'add':
            stats['total_added'] += tx['amount']
        elif tx['type'] in ['purchase', 'withdraw']:
            stats['total_spent'] += abs(tx['amount'])
        
        # Check if transaction is within last 30 days
        tx_date = datetime.strptime(tx['date'], '%Y-%m-%d')
        if tx_date >= thirty_days_ago:
            stats['transaction_count_30d'] += 1
    
    if transactions:
        stats['last_transaction'] = transactions[0]['date']
    
    return stats