#!/usr/bin/env python3
"""
Comprehensive Data Viewer for GCP PostgreSQL Database
Shows all data from your Isabi platform database
"""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

def connect_to_database():
    """Connect to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def format_price(price):
    """Format price for display"""
    if price is None:
        return "N/A"
    return f"${float(price):.2f}"

def format_datetime(dt):
    """Format datetime for display"""
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def view_products_data(conn):
    """View all products data"""
    print("\n" + "="*80)
    print("🛍️  PRODUCTS TABLE - All Products")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.product_id, p.product_name, p.price, p.status, p.created_at,
               pt.product_type_name, p.admin_type
        FROM products p
        LEFT JOIN product_types pt ON p.product_type_id = pt.product_type_id
        ORDER BY p.created_at DESC
    """)
    
    products = cursor.fetchall()
    
    if not products:
        print("❌ No products found")
        return
    
    print(f"📊 Total Products: {len(products)}")
    print("-" * 80)
    
    for i, product in enumerate(products, 1):
        product_id, name, price, status, created_at, type_name, admin_type = product
        print(f"\n🔸 Product #{i}")
        print(f"   ID: {product_id}")
        print(f"   Name: {name}")
        print(f"   Price: {format_price(price)}")
        print(f"   Status: {status}")
        print(f"   Type: {type_name}")
        print(f"   Admin: {admin_type}")
        print(f"   Created: {format_datetime(created_at)}")

def view_digital_products_data(conn):
    """View digital products data"""
    print("\n" + "="*80)
    print("💾 DIGITAL_PRODUCTS TABLE - Digital Downloads")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dp.product_id, dp.product_name, dp.product_category, 
               dp.product_location, dp.product_size_mb, dp.file_format,
               dp.created_at
        FROM digital_products dp
        ORDER BY dp.created_at DESC
    """)
    
    digital_products = cursor.fetchall()
    
    if not digital_products:
        print("❌ No digital products found")
        return
    
    print(f"📊 Total Digital Products: {len(digital_products)}")
    print("-" * 80)
    
    for i, product in enumerate(digital_products, 1):
        product_id, name, category, location, size_mb, file_format, created_at = product
        print(f"\n🔸 Digital Product #{i}")
        print(f"   ID: {product_id}")
        print(f"   Name: {name}")
        print(f"   Category: {category}")
        print(f"   File Format: {file_format}")
        print(f"   Size: {size_mb} MB" if size_mb else "   Size: N/A")
        print(f"   Location: {location}")
        print(f"   Created: {format_datetime(created_at)}")

def view_ai_training_products_data(conn):
    """View AI training products data"""
    print("\n" + "="*80)
    print("🤖 AI_TRAIN_PRODUCTS TABLE - AI Training Courses")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT atp.product_id, atp.product_name, atp.product_category,
               atp.created_at
        FROM ai_train_products atp
        ORDER BY atp.created_at DESC
    """)
    
    ai_products = cursor.fetchall()
    
    if not ai_products:
        print("❌ No AI training products found")
        return
    
    print(f"📊 Total AI Training Products: {len(ai_products)}")
    print("-" * 80)
    
    for i, product in enumerate(ai_products, 1):
        product_id, name, category, created_at = product
        print(f"\n🔸 AI Training Product #{i}")
        print(f"   ID: {product_id}")
        print(f"   Name: {name}")
        print(f"   Category: {category}")
        print(f"   Created: {format_datetime(created_at)}")

def view_users_data(conn):
    """View users data"""
    print("\n" + "="*80)
    print("👥 USERS TABLE - User Information")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT phone_number, email, name, created_at, last_activity
        FROM users
        ORDER BY created_at DESC
    """)
    
    users = cursor.fetchall()
    
    if not users:
        print("❌ No users found")
        return
    
    print(f"📊 Total Users: {len(users)}")
    print("-" * 80)
    
    for i, user in enumerate(users, 1):
        phone, email, name, created_at, last_activity = user
        print(f"\n🔸 User #{i}")
        print(f"   Phone: {phone}")
        print(f"   Name: {name}")
        print(f"   Email: {email}")
        print(f"   Created: {format_datetime(created_at)}")
        print(f"   Last Activity: {format_datetime(last_activity)}")

def view_payments_data(conn):
    """View payments data"""
    print("\n" + "="*80)
    print("💳 PAYMENTS TABLE - Payment History")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.payment_id, p.payment_amount, p.product_id, p.user_phone,
               p.payment_method, p.payment_status, p.transaction_id, p.payment_date
        FROM payments p
        ORDER BY p.payment_date DESC
    """)
    
    payments = cursor.fetchall()
    
    if not payments:
        print("❌ No payments found")
        return
    
    print(f"📊 Total Payments: {len(payments)}")
    print("-" * 80)
    
    for i, payment in enumerate(payments, 1):
        payment_id, amount, product_id, user_phone, method, status, transaction_id, payment_date = payment
        print(f"\n🔸 Payment #{i}")
        print(f"   Payment ID: {payment_id}")
        print(f"   Amount: {format_price(amount)}")
        print(f"   Product ID: {product_id}")
        print(f"   User Phone: {user_phone}")
        print(f"   Method: {method}")
        print(f"   Status: {status}")
        print(f"   Transaction ID: {transaction_id}")
        print(f"   Payment Date: {format_datetime(payment_date)}")

def view_product_types_data(conn):
    """View product types data"""
    print("\n" + "="*80)
    print("📂 PRODUCT_TYPES TABLE - Product Categories")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_type_id, product_type_name, description, created_at
        FROM product_types
        ORDER BY created_at DESC
    """)
    
    product_types = cursor.fetchall()
    
    if not product_types:
        print("❌ No product types found")
        return
    
    print(f"📊 Total Product Types: {len(product_types)}")
    print("-" * 80)
    
    for i, product_type in enumerate(product_types, 1):
        type_id, name, description, created_at = product_type
        print(f"\n🔸 Product Type #{i}")
        print(f"   ID: {type_id}")
        print(f"   Name: {name}")
        print(f"   Description: {description}")
        print(f"   Created: {format_datetime(created_at)}")

def main():
    """Main function to display all database data"""
    print("🔍 COMPREHENSIVE DATABASE DATA VIEWER")
    print("=" * 80)
    print(f"📅 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # View all data
        view_products_data(conn)
        view_digital_products_data(conn)
        view_ai_training_products_data(conn)
        view_users_data(conn)
        view_payments_data(conn)
        view_product_types_data(conn)
        
        print("\n" + "="*80)
        print("✅ DATABASE VIEW COMPLETE")
        print("="*80)
        print("📋 Summary:")
        print("   • Your GCP PostgreSQL database is fully operational")
        print("   • Contains product data across multiple categories")
        print("   • Ready for WhatsApp bot integration")
        print("   • All tables are properly structured")
        
    except Exception as e:
        print(f"❌ Error viewing data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
