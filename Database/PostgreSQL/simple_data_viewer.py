#!/usr/bin/env python3
"""
Simple Data Viewer for GCP PostgreSQL Database
"""

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

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

def main():
    """Main function to display all database data"""
    print("🔍 GCP POSTGRESQL DATABASE DATA VIEWER")
    print("=" * 80)
    print(f"📅 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # View Products Table
        print("\n" + "="*80)
        print("🛍️  PRODUCTS TABLE")
        print("="*80)
        cursor.execute("SELECT product_id, product_name, price, status, created_at FROM products ORDER BY created_at DESC")
        products = cursor.fetchall()
        print(f"📊 Total Products: {len(products)}")
        for i, product in enumerate(products, 1):
            product_id, name, price, status, created_at = product
            print(f"\n🔸 Product #{i}")
            print(f"   ID: {product_id}")
            print(f"   Name: {name}")
            print(f"   Price: {format_price(price)}")
            print(f"   Status: {status}")
            print(f"   Created: {format_datetime(created_at)}")
        
        # View Digital Products Table
        print("\n" + "="*80)
        print("💾 DIGITAL_PRODUCTS TABLE")
        print("="*80)
        cursor.execute("SELECT product_id, product_name, product_category, product_location, file_format FROM digital_products")
        digital_products = cursor.fetchall()
        print(f"�� Total Digital Products: {len(digital_products)}")
        for i, product in enumerate(digital_products, 1):
            product_id, name, category, location, file_format = product
            print(f"\n🔸 Digital Product #{i}")
            print(f"   ID: {product_id}")
            print(f"   Name: {name}")
            print(f"   Category: {category}")
            print(f"   Format: {file_format}")
            print(f"   Location: {location}")
        
        # View AI Training Products Table
        print("\n" + "="*80)
        print("🤖 AI_TRAIN_PRODUCTS TABLE")
        print("="*80)
        cursor.execute("SELECT product_id, product_name, product_category FROM ai_train_products")
        ai_products = cursor.fetchall()
        print(f"📊 Total AI Training Products: {len(ai_products)}")
        for i, product in enumerate(ai_products, 1):
            product_id, name, category = product
            print(f"\n🔸 AI Training Product #{i}")
            print(f"   ID: {product_id}")
            print(f"   Name: {name}")
            print(f"   Category: {category}")
        
        # View Users Table
        print("\n" + "="*80)
        print("👥 USERS TABLE")
        print("="*80)
        cursor.execute("SELECT phone_number, name, email, created_at FROM users")
        users = cursor.fetchall()
        print(f"📊 Total Users: {len(users)}")
        for i, user in enumerate(users, 1):
            phone, name, email, created_at = user
            print(f"\n🔸 User #{i}")
            print(f"   Phone: {phone}")
            print(f"   Name: {name}")
            print(f"   Email: {email}")
            print(f"   Created: {format_datetime(created_at)}")
        
        # View Payments Table
        print("\n" + "="*80)
        print("💳 PAYMENTS TABLE")
        print("="*80)
        cursor.execute("SELECT payment_id, payment_amount, user_phone, payment_status, payment_date FROM payments")
        payments = cursor.fetchall()
        print(f"📊 Total Payments: {len(payments)}")
        if payments:
            for i, payment in enumerate(payments, 1):
                payment_id, amount, user_phone, status, payment_date = payment
                print(f"\n🔸 Payment #{i}")
                print(f"   Payment ID: {payment_id}")
                print(f"   Amount: {format_price(amount)}")
                print(f"   User Phone: {user_phone}")
                print(f"   Status: {status}")
                print(f"   Date: {format_datetime(payment_date)}")
        else:
            print("❌ No payments found")
        
        # View Product Types Table
        print("\n" + "="*80)
        print("📂 PRODUCT_TYPES TABLE")
        print("="*80)
        cursor.execute("SELECT product_type_id, product_type_name, description FROM product_types")
        product_types = cursor.fetchall()
        print(f"📊 Total Product Types: {len(product_types)}")
        for i, product_type in enumerate(product_types, 1):
            type_id, name, description = product_type
            print(f"\n🔸 Product Type #{i}")
            print(f"   ID: {type_id}")
            print(f"   Name: {name}")
            print(f"   Description: {description}")
        
        print("\n" + "="*80)
        print("✅ DATABASE VIEW COMPLETE")
        print("="*80)
        print("📋 Summary:")
        print(f"   • Products: {len(products)}")
        print(f"   • Digital Products: {len(digital_products)}")
        print(f"   • AI Training Products: {len(ai_products)}")
        print(f"   • Users: {len(users)}")
        print(f"   • Payments: {len(payments)}")
        print(f"   • Product Types: {len(product_types)}")
        print("   • Your GCP PostgreSQL database is fully operational!")
        
    except Exception as e:
        print(f"❌ Error viewing data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
