# Flask Invoice Management System 💰

A comprehensive Flask-based invoice and inventory management system with customer wallet functionality, admin panel, purchase tracking and many more.

## 🚨 Important Notice
**This is a SAMPLE PROJECT for educational purposes only.**  
This application is NOT production-ready and should not be used in real-world scenarios without significant security enhancements and proper infrastructure setup.

## 📋 System Overview

This Flask application provides a complete e-commerce-like system with:

### 🔧 Core Features
- **Customer Management**: Registration, login, wallet setup
- **Product Inventory**: CRUD operations for products with stock management
- **Purchase System**: Buy products with "Buy 3 Get 1 Free" offers
- **Invoice Generation**: Automatic PDF invoice generation for purchases
- **Wallet System**: Virtual wallet with balance management
- **Admin Panel**: Complete admin interface for management
- **Sales Analytics**: Reports and insights for business intelligence

### 🛡️ Security Features (Basic)
- Session-based authentication
- Customer identity verification
- Card information validation
- Admin role-based access


## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd flask-invoice-app

2. Create virtual environment
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate


 3. Install dependencies
    pip install -r requirements.txt

 4. Initialize the database
    The system will automatically create necessary JSON files on first run
    Sample products and admin accounts are created automatically
 
 5. Run the app
    Python app.py

 6. Access the application
    Main site: http://localhost:xxxx
    Admin panel: http://localhost:xxxx/admin/login      
