'''
This module provides utility functions for handling product data,
saving inventory updates, and generating restock invoices.
'''

from datetime import datetime  # Import datetime for timestamp generation
from .read_ops import products  # Changed to relative import
import os
import json

# Update file paths for new structure
def get_invoice_path():
    """Get absolute path to invoices folder"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return os.path.join(parent_dir, 'invoices')

INVOICE_FOLDER = get_invoice_path()
PURCHASE_DB_FOLDER = os.path.join(INVOICE_FOLDER, 'purchase_database')
RESTOCK_DB_FOLDER = os.path.join(INVOICE_FOLDER, 'restock_database')

def create_folders():
    '''Create necessary folders if they don't exist'''
    folders = [INVOICE_FOLDER, PURCHASE_DB_FOLDER, RESTOCK_DB_FOLDER]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"✅ Created folder: {folder}")
        else:
            print(f"✅ Folder already exists: {folder}")

def datefunction():
    '''
    Generates a timestamp in the format YYYY-MM-DD.
    '''
    now = datetime.now()
    return f"{now.year}-{str(now.month).zfill(2)}-{str(now.day).zfill(2)}"

def datetimefunction():
    '''
    Generates a timestamp in the format YYYYMMDDHHMM for unique filenames.
    '''
    now = datetime.now()
    return str(now.year) + str(now.month).zfill(2) + str(now.day).zfill(2) + str(now.hour).zfill(2) + str(now.minute).zfill(2)

# REMOVE the save_products function completely since it's in read_ops.py
# def save_products():
#     '''
#     Saves the current product inventory to JSON (handled by read_ops now).
#     This function is kept for compatibility but the actual saving is done in read_ops.
#     '''
#     try:
#         from backend_engine.read_ops import save_products as save_products_json
#         return save_products_json()
#     except Exception as e:
#         print(f"Error saving products: {e}")
#         return False

def get_wallet_balance():
    '''Get current wallet balance from wallet.json'''
    try:
        wallet_file = '../database/wallets.json'  # Updated path
        if not os.path.exists(wallet_file):
            return 0
        
        with open(wallet_file, "r") as f:
            wallets = json.load(f)
            # Return first wallet balance or 0 if no wallets
            if wallets:
                first_wallet = list(wallets.values())[0]
                return first_wallet.get('balance', 0)
            return 0
    except Exception as e:
        print(f"Error reading wallet: {e}")
        return 0

def update_wallet(amount):
    '''Update wallet balance'''
    try:
        wallet_file = '../database/wallets.json'  # Updated path
        if not os.path.exists(wallet_file):
            return amount
        
        with open(wallet_file, "r") as f:
            wallets = json.load(f)
        
        if wallets:
            # Update first wallet (for compatibility)
            first_key = list(wallets.keys())[0]
            current_balance = wallets[first_key].get('balance', 0)
            new_balance = current_balance + amount
            wallets[first_key]['balance'] = new_balance
            
            with open(wallet_file, "w") as f:
                json.dump(wallets, f, indent=2)
            
            return new_balance
        return amount
    except Exception as e:
        print(f"Error updating wallet: {e}")
        return 0

def save_purchase_invoice(customer_name, items, total, timestamp):
    '''Save purchase invoice to purchase_database folder with proper naming'''
    create_folders()
    
    # Generate invoice content
    invoice_content = f"{'-' * 50}\n"
    invoice_content += f"INVOICE - {timestamp}\n"
    invoice_content += f"Customer: {customer_name}\n"
    invoice_content += f"{'-' * 50}\n"
    invoice_content += "Item\t\tQty\tFree\tPrice\n"
    invoice_content += f"{'-' * 50}\n"
    
    for item in items:
        invoice_content += f"{item['name']}\t{item['qty']}\t{item['free']}\t₹{item['price']:.2f}\n"
    
    invoice_content += f"{'-' * 50}\n"
    invoice_content += f"TOTAL:\t\t\t\t₹{total:.2f}\n"
    invoice_content += f"{'-' * 50}\n"
    
    # Create proper filename
    if items:
        first_item = items[0]['name'].replace(' ', '_').lower()
        if len(items) > 1:
            item_part = f"{first_item}_and_{len(items)-1}_more"
        else:
            item_part = first_item
    else:
        item_part = "purchase"
    
    filename = f"{customer_name.replace(' ', '_')}_{item_part}_{timestamp.replace('-', '')}.txt"
    filepath = os.path.join(PURCHASE_DB_FOLDER, filename)
    
    try:
        with open(filepath, "w", encoding='utf-8') as f:
            f.write(invoice_content)
        print(f"✅ Purchase invoice saved: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving purchase invoice: {e}")
        return None

def generate_restock_invoice(session_items, vendor_name, total_cost):
    '''
    Generates a restock invoice based on the supplied items and vendor details.
    Saves the invoice to restock_database folder with proper naming.
    '''
    create_folders()
    
    timestamp = datefunction()  # Get formatted date
    unique_id = datetimefunction()  # Get unique ID for filename
    
    invoice = "-" * 50 + "\n"
    invoice += f"RESTOCK INVOICE - {timestamp}\n"
    invoice += f"Vendor: {vendor_name}\n"
    invoice += "-" * 50 + "\n"
    invoice += "Product\t\tBrand\t\tQty\tRate\tAmount\n"
    invoice += "-" * 50 + "\n"

    grand_total = 0
    restocked_items = []
    
    for item in session_items:
        product_id = item[0]
        amount = item[1]
        item_cost = item[2]
        p = products[str(product_id)]  # Ensure string key

        invoice += (
            p["name"] + "\t" +
            p["brand"] + "\t" +
            str(amount) + "\t" +
            f"₹{p['cost']:.2f}" + "\t" +
            f"₹{item_cost:.2f}" + "\n"
        )
        grand_total += item_cost
        restocked_items.append(p["name"].replace(' ', '_').lower())

    invoice += "-" * 50 + "\n"
    invoice += f"TOTAL:\t\t\t\t\t\t₹{grand_total:.2f}\n"
    invoice += "-" * 50 + "\n"

    # Create proper filename for restock
    if restocked_items:
        if len(restocked_items) == 1:
            items_part = restocked_items[0]
        elif len(restocked_items) == 2:
            items_part = f"{restocked_items[0]}_and_{restocked_items[1]}"
        else:
            items_part = f"{restocked_items[0]}_and_{len(restocked_items)-1}_more"
    else:
        items_part = "restock"
    
    filename = f"{vendor_name.replace(' ', '_')}_{items_part}_{timestamp.replace('-', '')}.txt"
    filepath = os.path.join(RESTOCK_DB_FOLDER, filename)
    
    try:
        with open(filepath, "w", encoding='utf-8') as f:
            f.write(invoice)
        print(f"✅ Restock invoice saved: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving restock invoice: {e}")
        return None