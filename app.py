from flask import Flask, render_template, request, redirect, url_for, flash, session
from backend_engine.read_ops import load_products, save_products, add_product, update_product, delete_product, reload_products, products, update_product_stock
from backend_engine.write_ops import generate_restock_invoice, datefunction, save_purchase_invoice
from backend_engine.customer_ops import register_customer, login_customer, get_customer, update_customer_purchase, get_all_customers, get_wallet_balance, update_wallet_balance, setup_customer_wallet, get_customer_wallet, verify_customer_identity, verify_card_information, get_customer_transactions, get_transaction_stats, init_transaction_history
from backend_engine.admin_ops import authenticate_admin, get_admin, create_admin, get_all_admins
import json
import os
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'your_secret_key_here'

# ======== PROPER INITIALIZATION ========
print("🚀 Starting application - Loading products...")
load_products()
reload_products()
print(f"✅ Application started with {len(products)} products")

# Force initialize transaction database
init_transaction_history()
print("✅ Transaction database initialized")
# =====================================

def get_products_from_file():
    """Always read products directly from JSON file"""
    try:
        # Use absolute path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        products_file = os.path.join(parent_dir, 'database', 'products.json')
        
        print(f"🔄 DEBUG: Looking for products at: {products_file}")
        print(f"🔄 DEBUG: File exists: {os.path.exists(products_file)}")
        
        with open(products_file, 'r') as f:
            products_data = json.load(f)
        
        print(f"✅ DEBUG: Successfully read {len(products_data)} products from file")
        
        # Debug: Show what products were found
        for product_id, product in products_data.items():
            print(f"🔄 DEBUG Product {product_id}: {product['name']} - Active: {product.get('is_active', True)}")
        
        return products_data
    except Exception as e:
        print(f"❌ Error reading products file: {e}")
        return {}

def ensure_products_reload():
    """Ensure products are reloaded from file before any product operation"""
    from backend_engine.read_ops import load_products
    return load_products(force=True)

@app.route('/')
def index():
    # Only show wallet balance if customer is logged in
    wallet_balance = 0
    if 'customer_id' in session:
        wallet_balance = get_wallet_balance(session['customer_id'])
    return render_template('index.html', wallet_balance=wallet_balance)

@app.route('/products')
def show_products():
    """Display all products - FIXED: Always reload before display"""
    wallet_balance = 0
    if 'customer_id' in session:
        wallet_balance = get_wallet_balance(session['customer_id'])
    
    # CRITICAL FIX: Always reload products before displaying
    ensure_products_reload()
    
    products_list = []
    for product_id, p in products.items():
        # Only include active products
        if p.get('is_active', True):
            products_list.append({
                'id': p['id'],
                'name': p['name'],
                'brand': p['brand'],
                'category': p.get('category', 'Skincare'),
                'stock': p['stock'],
                'price': p['price'],
                'country': p['country'],
                'description': p.get('description', '')
            })
    
    print(f"🔄 DEBUG PRODUCTS: Displaying {len(products_list)} products")
    return render_template('products.html', products=products_list, wallet_balance=wallet_balance)

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    """Handle customer purchases with verification - FIXED: Proper product reloading"""
    if 'customer_id' not in session:
        flash('Please login to make a purchase.', 'error')
        return redirect(url_for('login'))
    
    wallet_balance = get_wallet_balance(session['customer_id'])
    customer_wallet = get_customer_wallet(session['customer_id'])
    
    if request.method == 'POST':
        # Step 2: Verification and purchase processing
        verify_name = request.form.get('verify_name')
        verify_email = request.form.get('verify_email')
        verify_phone = request.form.get('verify_phone')
        verify_card_holder = request.form.get('verify_card_holder')
        verify_card_last_four = request.form.get('verify_card_last_four')
        
        # Verify identity
        identity_result = verify_customer_identity(
            session['customer_id'], 
            verify_name, 
            verify_email, 
            verify_phone
        )
        
        if not identity_result['success']:
            flash(identity_result['error'], 'error')
            return redirect(url_for('purchase'))
        
        # Verify card information
        card_result = verify_card_information(
            session['customer_id'],
            verify_card_holder,
            verify_card_last_four
        )
        
        if not card_result['success']:
            flash(card_result['error'], 'error')
            return redirect(url_for('purchase'))
        
        # Collect purchased items from hidden fields
        purchased_items = []
        for key, value in request.form.items():
            if key.startswith('product_') and value.isdigit():
                product_id = int(key.split('_')[1])
                quantity = int(value)
                if quantity > 0:
                    purchased_items.append((product_id, quantity))
        
        if not purchased_items:
            flash('No products selected for purchase!', 'error')
            return redirect(url_for('purchase'))
        
        # CRITICAL: Reload products to get latest stock before processing
        ensure_products_reload()
        
        # Process purchase using the new stock update function
        try:
            total = 0
            items = []
            
            # FIRST: Check stock availability for all items
            for product_id, qty in purchased_items:
                if str(product_id) in products:
                    p = products[str(product_id)]
                    free = qty // 3  # Buy 3 get 1 free
                    required = qty + free
                    
                    if required > p["stock"]:
                        flash(f'Not enough stock for {p["name"]}. Available: {p["stock"]}', 'error')
                        return redirect(url_for('purchase'))
                    
                    price = p["cost"] * 2 * qty
                    items.append({
                        "name": p["name"],
                        "qty": qty,
                        "free": free,
                        "price": price
                    })
                    total += price
            
            # Check wallet balance
            if total > wallet_balance:
                flash(f'Insufficient wallet balance! Total: ₹{total}, Available: ₹{wallet_balance}', 'error')
                return redirect(url_for('purchase'))
            
            # SECOND: Update stock for all items using the new function
            stock_updates = []
            print(f"🛒 DEBUG: Starting stock updates for {len(purchased_items)} items")

            for product_id, qty in purchased_items:
                p = products[str(product_id)]
                free = qty // 3
                required = qty + free
                
                print(f"🛒 DEBUG: Updating product {product_id} ({p['name']})")
                print(f"🛒 DEBUG: Qty: {qty}, Free: {free}, Required: {required}, Current Stock: {p['stock']}")

                # Use the new stock update function
                stock_result = update_product_stock(product_id, -required)

                if not stock_result['success']:
                    flash(f'Error updating stock for {p["name"]}: {stock_result["error"]}', 'error')
                    return redirect(url_for('purchase'))
                
                stock_updates.append({
                    'product_id': product_id,
                    'product_name': p['name'],
                    'quantity': qty,
                    'free_quantity': free,
                    'total_quantity': required
                })
            print(f"🛒 DEBUG: Completed all stock updates")
            
            # Generate invoice with proper date format
            timestamp = datefunction()
            
            # Save invoice using new function
            filename = save_purchase_invoice(verify_name, items, total, timestamp)
            
            if filename:
                # Update customer wallet (deduct)
                new_balance = update_wallet_balance(session['customer_id'], -total)

                # Update customer purchase history
                update_customer_purchase(session['customer_id'], total)

                # LOG PURCHASE TRANSACTION
                from backend_engine.customer_ops import log_customer_transaction
                log_customer_transaction(
                    session['customer_id'],
                    'purchase',
                    total,
                    f'Purchase: {len(purchased_items)} items',
                    new_balance
                )

                # LOG SALES FOR ANALYTICS
                from backend_engine.admin_ops import log_sale
                for product_id, qty in purchased_items:
                    if str(product_id) in products:
                        p = products[str(product_id)]
                        # Log each product sale
                        log_sale(
                            customer_id=session['customer_id'],
                            product_id=product_id,
                            product_name=p['name'],
                            quantity=qty,
                            unit_price=p['cost'] * 2,
                            total_price=p['cost'] * 2 * qty,
                            timestamp=timestamp
                        )
                
                # Log transaction
                from backend_engine.admin_ops import log_transaction
                log_transaction(
                    customer_id=session['customer_id'],
                    amount=total,
                    transaction_type='revenue',
                    description=f'Purchase: {len(purchased_items)} items'
                )

                # Transfer money to admin wallet
                from backend_engine.admin_ops import add_revenue_to_admin
                admin_wallet_update = add_revenue_to_admin(total)

                if admin_wallet_update:
                    print(f"✅ ₹{total} transferred to admin wallet. New balance: ₹{admin_wallet_update['balance']}")
                else:
                    print("❌ Failed to update admin wallet")
                
                # Store invoice data for display
                session['invoice_data'] = {
                    'customer_name': verify_name,
                    'timestamp': timestamp,
                    'items': items,
                    'total': total,
                    'filename': filename,
                    'wallet_balance': get_wallet_balance(session['customer_id'])
                }
                
                flash('Purchase completed successfully! Identity and card verified.', 'success')
                return redirect(url_for('invoice'))
            else:
                flash('Error generating invoice!', 'error')
            
        except Exception as e:
            flash(f'Error during purchase: {str(e)}', 'error')
    
    # For GET request - show products with purchase form
    # CRITICAL: Reload products to ensure we have latest stock data
    ensure_products_reload()
    
    products_list = []
    for product_id, p in products.items():
        if p.get('is_active', True):
            products_list.append({
                'id': product_id,
                'name': p['name'],
                'brand': p['brand'],
                'stock': p['stock'],
                'price': p['price'],
                'country': p['country']
            })
    
    return render_template('purchase.html', 
                         products=products_list, 
                         wallet_balance=wallet_balance,
                         customer_wallet=customer_wallet)

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    """Wallet management page"""
    if 'customer_id' not in session:
        flash('Please login to access your wallet.', 'error')
        return redirect(url_for('login'))
    
    customer = get_customer(session['customer_id'])
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        amount = float(request.form.get('amount', 0))
        
        if action == 'add':
            update_wallet_balance(session['customer_id'], amount)
            flash(f'₹{amount} added to wallet!', 'success')
        elif action == 'withdraw':
            current_balance = get_wallet_balance(session['customer_id'])
            if amount > current_balance:
                flash('Insufficient balance for withdrawal!', 'error')
            else:
                update_wallet_balance(session['customer_id'], -amount)
                flash(f'₹{amount} withdrawn from wallet!', 'success')
    
    # Refresh customer data after wallet update
    customer = get_customer(session['customer_id'])
    
    # Get transaction history and stats
    transactions = get_customer_transactions(session['customer_id'], limit=20)
    tx_stats = get_transaction_stats(session['customer_id'])
    
    return render_template('wallet.html', 
                         customer=customer, 
                         transactions=transactions,
                         tx_stats=tx_stats)

@app.route('/admin/restock', methods=['GET', 'POST'])
def admin_restock():
    """Admin restock page - FIXED: Simplified synchronization"""
    if 'admin_id' not in session:
        flash('Please login as admin to access restock.', 'error')
        return redirect(url_for('admin_login'))
    
    from backend_engine.admin_ops import get_admin_wallet, deduct_admin_balance
    from backend_engine.read_ops import update_product_stock, products
    
    admin_wallet = get_admin_wallet()
    
    if request.method == 'POST':
        vendor_name = request.form.get('vendor_name')
        
        if not vendor_name:
            flash('Please enter vendor name!', 'error')
            return redirect(url_for('admin_restock'))
        
        # Collect restock items
        restock_items = []
        for key, value in request.form.items():
            if key.startswith('qty_') and value.isdigit():
                product_id = int(key.split('_')[1])
                quantity = int(value)
                if quantity > 0:
                    restock_items.append((product_id, quantity))
        
        if not restock_items:
            flash('Please select at least one product to restock!', 'error')
            return redirect(url_for('admin_restock'))
        
        # Process restock - SIMPLIFIED APPROACH
        try:
            total_cost = 0
            stock_updates = []
            
            print(f"🔄 RESTOCK: Starting restock with {len(restock_items)} items")
            
            # Calculate total cost first
            for product_id, amount in restock_items:
                product_id_str = str(product_id)
                if product_id_str in products:
                    cost = amount * products[product_id_str]["cost"]
                    total_cost += cost
                    stock_updates.append({
                        'product_id': product_id,
                        'amount': amount,
                        'cost': cost,
                        'product_name': products[product_id_str]["name"]
                    })
                else:
                    flash(f'Product ID {product_id} not found!', 'error')
                    return redirect(url_for('admin_restock'))
            
            print(f"💰 RESTOCK: Total cost: ₹{total_cost}")
            
            # Check admin wallet balance
            if total_cost > admin_wallet['balance']:
                flash(f'Insufficient admin balance! Total Cost: ₹{total_cost}, Available: ₹{admin_wallet["balance"]}', 'error')
                return redirect(url_for('admin_restock'))
            
            # Update stock for all items
            print(f"📦 RESTOCK: Starting stock updates")
            
            for update in stock_updates:
                product_id = update['product_id']
                amount = update['amount']
                product_name = update['product_name']
                
                print(f"📦 RESTOCK: Updating {product_name} (+{amount})")
                
                # Use the stock update function
                stock_result = update_product_stock(product_id, amount)
                
                if not stock_result['success']:
                    flash(f'Error restocking {product_name}: {stock_result["error"]}', 'error')
                    return redirect(url_for('admin_restock'))
                else:
                    print(f"✅ RESTOCK: Successfully updated {product_name}")
            
            # Deduct from admin wallet
            admin_wallet_update = deduct_admin_balance(total_cost)
            
            if admin_wallet_update:
                print(f"✅ RESTOCK: Admin wallet updated")
                flash(f'Restocking completed successfully! ₹{total_cost} deducted from admin wallet.', 'success')
            else:
                print("⚠️ RESTOCK: Failed to update admin wallet")
                flash('Restocking completed but failed to update admin wallet.', 'warning')
            
            # Generate restock invoice
            if stock_updates:
                # Convert to session_items format for invoice
                session_items = []
                for update in stock_updates:
                    session_items.append([update['product_id'], update['amount'], update['cost']])
                
                invoice_success = generate_restock_invoice(session_items, vendor_name, total_cost)
                print(f"📄 RESTOCK: Invoice generated: {invoice_success}")
            
            # Force reload products to ensure consistency
            from backend_engine.read_ops import load_products
            load_products(force=True)
            
            print("✅ RESTOCK: Process completed successfully")
            return redirect(url_for('admin_restock'))
            
        except Exception as e:
            print(f"❌ RESTOCK ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Error during restocking: {str(e)}', 'error')
    
    # For GET request - show products with restock form
    # Use simple reload instead of ensure_products_reload
    from backend_engine.read_ops import load_products
    load_products()
    
    products_list = []
    for product_id, p in products.items():
        if p.get('is_active', True):
            products_list.append({
                'id': product_id,
                'name': p['name'],
                'brand': p['brand'],
                'stock': p['stock'],
                'cost': p['cost'],
                'country': p['country']
            })
    
    print(f"🔄 RESTOCK: Displaying {len(products_list)} products")
    
    return render_template('admin_restock.html', 
                         products=products_list, 
                         admin_wallet=admin_wallet,
                         wallet_balance=admin_wallet['balance'])

@app.route('/setup-wallet', methods=['GET', 'POST'])
def setup_wallet():
    """Setup customer wallet"""
    if 'customer_id' not in session:
        flash('Please login to setup your wallet.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        card_type = request.form.get('card_type')
        card_holder = request.form.get('card_holder')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        
        if not all([card_type, card_holder, card_number, expiry_date]):
            flash('Please fill all wallet fields!', 'error')
            return redirect(url_for('setup_wallet'))
        
        wallet_data = {
            'card_type': card_type,
            'card_holder': card_holder,
            'card_number': card_number,
            'expiry_date': expiry_date
        }
        
        if setup_customer_wallet(session['customer_id'], wallet_data):
            flash('Wallet setup successful! ₹10,000 has been added to your account.', 'success')
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Error setting up wallet. Please try again.', 'error')
    
    return render_template('setup_wallet.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Customer registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        setup_wallet = request.form.get('setup_wallet') == 'on'
        
        if not all([name, email, phone, password]):
            flash('Please fill all required fields!', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        
        wallet_data = None
        if setup_wallet:
            card_type = request.form.get('card_type')
            card_holder = request.form.get('card_holder')
            card_number = request.form.get('card_number')
            expiry_date = request.form.get('expiry_date')
            
            if not all([card_type, card_holder, card_number, expiry_date]):
                flash('Please fill all wallet fields!', 'error')
                return redirect(url_for('register'))
            
            wallet_data = {
                'card_type': card_type,
                'card_holder': card_holder,
                'card_number': card_number,
                'expiry_date': expiry_date
            }
        
        result = register_customer(name, email, phone, password, setup_wallet, wallet_data)
        
        if result['success']:
            if setup_wallet:
                flash('Registration successful! ₹10,000 has been added to your wallet.', 'success')
            else:
                flash('Registration successful! Please setup your wallet to make purchases.', 'success')
            return redirect(url_for('login'))
        else:
            flash(result['error'], 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Customer login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            flash('Please fill all fields!', 'error')
            return redirect(url_for('login'))
        
        result = login_customer(email, password)
        
        if result['success']:
            session['customer_id'] = result['customer']['customer_id']
            session['customer_name'] = result['customer']['name']
            flash(f'Welcome back, {result["customer"]["name"]}!', 'success')
            return redirect(url_for('customer_dashboard'))
        else:
            flash(result['error'], 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Customer logout"""
    session.pop('customer_id', None)
    session.pop('customer_name', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def customer_dashboard():
    """Customer dashboard"""
    if 'customer_id' not in session:
        flash('Please login to access your dashboard.', 'error')
        return redirect(url_for('login'))
    
    customer = get_customer(session['customer_id'])
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('login'))
    
    return render_template('customer_dashboard.html', customer=customer)

@app.route('/customer/purchases')
def customer_purchases():
    """Customer purchase history"""
    if 'customer_id' not in session:
        flash('Please login to view your purchases.', 'error')
        return redirect(url_for('login'))
    
    from backend_engine.customer_ops import get_customer, get_customer_purchase_history
    
    customer = get_customer(session['customer_id'])
    purchase_history = get_customer_purchase_history(session['customer_id'])
    
    return render_template('customer_purchases.html', 
                         customer=customer, 
                         purchase_history=purchase_history)

@app.route('/invoice')
def invoice():
    """Display purchase invoice"""
    invoice_data = session.get('invoice_data')
    if not invoice_data:
        flash('No invoice data found!', 'error')
        return redirect(url_for('index'))
    
    return render_template('invoice.html', **invoice_data)

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    # If already logged in as admin, redirect to dashboard
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not all([username, password]):
            flash('Please fill all fields!', 'error')
            return redirect(url_for('admin_login'))
        
        result = authenticate_admin(username, password)
        
        if result['success']:
            session['admin_id'] = result['admin']['admin_id']
            session['admin_name'] = result['admin']['full_name']
            session['admin_role'] = result['admin']['role']
            flash(f'Welcome back, {result["admin"]["full_name"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash(result['error'], 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('admin_role', None)
    flash('You have been logged out from admin panel.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    if 'admin_id' not in session:
        flash('Please login as admin to access the dashboard.', 'error')
        return redirect(url_for('admin_login'))
    
    admin = get_admin(session['admin_id'])
    if not admin:
        flash('Admin not found!', 'error')
        return redirect(url_for('admin_login'))
    
    # Get basic stats - USE FILE READING FOR PRODUCTS
    from backend_engine.customer_ops import get_all_customers
    from backend_engine.admin_ops import get_admin_wallet
    
    total_customers = len(get_all_customers())
    total_products = len(products)
    total_stock = sum(product['stock'] for product in products.values())
    admin_wallet = get_admin_wallet()
    
    return render_template('admin_dashboard.html', 
                         admin=admin,
                         total_customers=total_customers,
                         total_products=total_products,
                         total_stock=total_stock,
                         admin_wallet=admin_wallet)

@app.route('/delete-account', methods=['GET', 'POST'])
def delete_account():
    """Customer account deletion"""
    if 'customer_id' not in session:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('login'))
    
    from backend_engine.customer_ops import delete_customer_account, get_customer
    
    customer = get_customer(session['customer_id'])
    
    if request.method == 'POST':
        confirm_password = request.form.get('confirm_password')
        confirm_deletion = request.form.get('confirm_deletion')
        
        if not confirm_password:
            flash('Please enter your password to confirm deletion.', 'error')
            return redirect(url_for('delete_account'))
        
        if not confirm_deletion:
            flash('Please confirm that you understand this action is permanent.', 'error')
            return redirect(url_for('delete_account'))
        
        result = delete_customer_account(session['customer_id'], confirm_password)
        
        if result['success']:
            # Logout and clear session
            session.pop('customer_id', None)
            session.pop('customer_name', None)
            flash(result['message'], 'success')
            return redirect(url_for('index'))
        else:
            flash(result['error'], 'error')
    
    return render_template('delete_account.html', customer=customer)

@app.route('/admin/customers')
def admin_customers():
    """Admin customers management"""
    if 'admin_id' not in session:
        flash('Please login as admin to view customers.', 'error')
        return redirect(url_for('admin_login'))
    
    customers = get_all_customers()
    
    return render_template('admin_customers.html', customers=customers)

@app.route('/admin/sales-reports')
def admin_sales_reports():
    """Sales reports and analytics"""
    if 'admin_id' not in session:
        flash('Please login as admin to view sales reports.', 'error')
        return redirect(url_for('admin_login'))
    
    from backend_engine.admin_ops import get_sales_analytics, get_daily_sales, get_top_products, get_customer_insights
    
    analytics = get_sales_analytics()
    daily_sales = get_daily_sales()
    top_products = get_top_products()
    customer_insights = get_customer_insights()
    
    return render_template('admin_sales_reports.html',
                         analytics=analytics,
                         daily_sales=daily_sales,
                         top_products=top_products,
                         customer_insights=customer_insights)

@app.route('/admin/products')
def admin_products():
    """Admin products management - FIXED: Proper product reloading"""
    if 'admin_id' not in session:
        flash('Please login as admin.', 'error')
        return redirect(url_for('admin_login'))
    
    # CRITICAL: Always reload products before displaying
    ensure_products_reload()
    
    # Get all active products from global products
    active_products = []
    for product_id, product in products.items():
        if product.get('is_active', True):
            active_products.append(product)
    
    print(f"🔄 ADMIN PRODUCTS: Displaying {len(active_products)} products")
    return render_template('admin_products.html', products=active_products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    """Add new product"""
    if 'admin_id' not in session:
        flash('Please login as admin.', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        # Get form data
        product_data = {
            'name': request.form.get('name'),
            'brand': request.form.get('brand'),
            'category': request.form.get('category', 'Skincare'),
            'stock': int(request.form.get('stock', 0)),
            'cost': float(request.form.get('cost', 0)),
            'country': request.form.get('country', ''),
            'description': request.form.get('description', '')
        }
        
        # Add product
        result = add_product(product_data)
        
        if result['success']:
            flash(f"Product '{product_data['name']}' added successfully!", 'success')
            return redirect(url_for('admin_products'))
        else:
            flash(f"Error adding product: {result['error']}", 'error')
    
    return render_template('admin_add_product.html')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    """Edit existing product"""
    if 'admin_id' not in session:
        flash('Please login as admin.', 'error')
        return redirect(url_for('admin_login'))
    
    # CRITICAL: Reload products before editing
    ensure_products_reload()
    
    product = products.get(str(product_id))
    
    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('admin_products'))
    
    if request.method == 'POST':
        # Get form data
        product_data = {
            'name': request.form.get('name'),
            'brand': request.form.get('brand'),
            'category': request.form.get('category'),
            'stock': int(request.form.get('stock', 0)),
            'cost': float(request.form.get('cost', 0)),
            'country': request.form.get('country', ''),
            'description': request.form.get('description', '')
        }
        
        # Update product
        result = update_product(product_id, product_data)
        
        if result['success']:
            flash(f"Product '{product_data['name']}' updated successfully!", 'success')
            return redirect(url_for('admin_products'))
        else:
            flash(f"Error updating product: {result['error']}", 'error')
    
    return render_template('admin_edit_product.html', product=product)

@app.route('/admin/products/delete/<int:product_id>')
def admin_delete_product(product_id):
    """Delete product"""
    if 'admin_id' not in session:
        flash('Please login as admin.', 'error')
        return redirect(url_for('admin_login'))
    
    # CRITICAL: Reload products before deletion
    ensure_products_reload()
    
    product = products.get(str(product_id))
    
    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('admin_products'))
    
    result = delete_product(product_id)
    
    if result['success']:
        flash(f"Product '{product['name']}' deleted successfully!", 'success')
    else:
        flash(f"Error deleting product: {result['error']}", 'error')
    
    return redirect(url_for('admin_products'))

@app.route('/debug/products')
def debug_products():
    """Debug endpoint to check product synchronization"""
    ensure_products_reload()
    
    products_list = []
    for product_id, p in products.items():
        products_list.append({
            'id': p['id'],
            'name': p['name'],
            'stock': p['stock'],
            'active': p.get('is_active', True)
        })
    
    return {
        'total_products': len(products_list),
        'products': products_list,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
if __name__ == '__main__':
    app.run(debug=True)