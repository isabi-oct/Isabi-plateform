# Enhanced Isabi WhatsApp Sales Bot - AI-Integrated Main Application
import os
import logging
import requests
import uvicorn
import threading
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, Query, Response, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Database imports
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# AI imports
import google.generativeai as genai
from dotenv import load_dotenv

# Import AI system

# Import Enhanced AI Conversation Service\nfrom Backend.services.ai_conversation import AIConversationService
from Backend.core.ai import ai_controller, prompt_manager

# Import GCP Vector Search
from Database.VectorDB import gcp_vector_client
from Backend.config.gcp_config import gcp_config

# Load environment variables
load_dotenv('Config/.env')

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --------------------
# GEMINI AI CONFIGURATION
# --------------------
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        # Initialize AI controller with Gemini model
        ai_controller.model = model
        logger.info("🤖 Gemini AI configured successfully")

# Initialize Enhanced AI Conversation Service\nai_conversation_service = AIConversationService()\nlogger.info("🤖 Enhanced AI Conversation Service initialized")
    else:
        logger.warning("⚠️ No Gemini API key found - using fallback responses")
        model = None
except Exception as e:
    logger.error(f"❌ Error configuring Gemini AI: {e}")
    model = None

# --------------------
# GCP VECTOR SEARCH CONFIGURATION
# --------------------
try:
    # Initialize GCP Vector Search client
    project_id = gcp_config.get_project_id()
    if project_id:
        gcp_vector_client.project_id = project_id
        logger.info(f"🔍 GCP Vector Search configured for project: {project_id}")
        logger.info(f"📊 Available indexes: {list(gcp_config.get_indexes().keys())}")
    else:
        logger.warning("⚠️ No GCP project ID found - Vector Search disabled")
except Exception as e:
    logger.error(f"❌ Error configuring GCP Vector Search: {e}")

# --------------------
# DATABASE CONNECTION
# --------------------
if not DATABASE_URL:
    logger.error("❌ DATABASE_URL not found in environment variables!")
    exit(1)

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("✅ PostgreSQL database connected successfully")
except Exception as e:
    logger.error(f"❌ Database connection failed: {e}")
    exit(1)

# --------------------
# PRODUCT DATA LOADING
# --------------------
PRODUCTS_DATABASE = {}
PRODUCT_CATEGORIES = set()

def load_products_from_database():
    """Load products from PostgreSQL database"""
    global PRODUCTS_DATABASE, PRODUCT_CATEGORIES
    
    try:
        with engine.connect() as connection:
            # Load products
            result = connection.execute(text("""
                SELECT p.product_id, p.product_name, p.product_type_name, p.price, p.status,
                       p.created_at, p.updated_at
                FROM products p
                
                WHERE p.status = 'active'
                ORDER BY p.created_at DESC
            """))
            
            products = result.fetchall()
            
            for product in products:
                product_id = str(product.product_id)
                PRODUCTS_DATABASE[product_id] = {
                    "id": product_id,
                    "name": product.product_name,
                    "description": product.product_type_name,
                    "price": float(product.price) if product.price else 0.0,
                    "category": product.product_type_name or "General",
                    "image_url": None,
                    "is_active": product.status == "active",
                    "product_type": product.product_type_name,
                    "created_at": product.created_at.isoformat() if product.created_at else None,
                    "updated_at": product.updated_at.isoformat() if product.updated_at else None
                }
                
                if product.product_type_name:
                    PRODUCT_CATEGORIES.add(product.product_type_name)
            
            logger.info(f"✅ Loaded {len(PRODUCTS_DATABASE)} products from database")
            logger.info(f"📂 Categories: {', '.join(PRODUCT_CATEGORIES)}")
            
    except Exception as e:
        logger.error(f"❌ Error loading products from database: {e}")
        PRODUCTS_DATABASE = {}

# Load products
load_products_from_database()

# --------------------
# FASTAPI APPLICATION
# --------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Isabi WhatsApp Sales Bot...")
    yield
    # Shutdown
    logger.info("🛑 Shutting down Isabi WhatsApp Sales Bot...")

app = FastAPI(
    title="Isabi WhatsApp Sales Bot",
    description="AI-powered WhatsApp sales bot with PostgreSQL and GCP Vector Search",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# API ENDPOINTS
# --------------------

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Isabi WhatsApp Sales Bot API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "AI-powered conversations",
            "PostgreSQL database",
            "GCP Vector Search",
            "WhatsApp integration",
            "Product catalog"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "products_loaded": len(PRODUCTS_DATABASE),
        "categories": list(PRODUCT_CATEGORIES),
        "ai_enabled": model is not None,
        "vector_search_enabled": gcp_config.get_project_id() is not None
    }

@app.get("/products")
async def get_products():
    """Get all products"""
    return {
        "status": "success",
        "products": list(PRODUCTS_DATABASE.values()),
        "total": len(PRODUCTS_DATABASE),
        "categories": list(PRODUCT_CATEGORIES)
    }

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get specific product"""
    if product_id in PRODUCTS_DATABASE:
        return {
            "status": "success",
            "product": PRODUCTS_DATABASE[product_id]
        }
    else:
        return {
            "status": "error",
            "message": "Product not found"
        }

@app.get("/ai/config")
async def get_ai_config():
    """Get current AI configuration"""
    try:
        return prompt_manager.get_current_config()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/ai/config")
async def update_ai_config(config: dict):
    """Update AI configuration"""
    try:
        ai_controller.update_prompt_config(config)
        return {"status": "success", "message": "AI configuration updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/vector/indexes")
async def get_vector_indexes():
    """Get available GCP Vector Search indexes"""
    try:
        indexes = gcp_config.get_indexes()
        return {
            "status": "success",
            "indexes": indexes,
            "default_index": gcp_config.get_default_index()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/vector/collections")
async def get_vector_collections():
    """Get available vector collections"""
    try:
        collections = gcp_vector_client.list_collections()
        return {
            "status": "success",
            "collections": collections
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/vector/query")
async def query_vector_search(query_data: dict):
    """Query GCP Vector Search"""
    try:
        collection_name = query_data.get("collection", "isabi_products")
        query_text = query_data.get("query", "")
        n_results = query_data.get("n_results", 5)
        
        results = gcp_vector_client.query_collection(collection_name, query_text, n_results)
        return {
            "status": "success",
            "results": results,
            "collection": collection_name
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --------------------
# WHATSAPP WEBHOOK ENDPOINTS
# --------------------

@app.get("/api/whatsapp/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """WhatsApp webhook verification"""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        return int(hub_challenge)
    else:
        logger.error("❌ Webhook verification failed")
        return {"error": "Verification failed"}, 403

@app.post("/api/whatsapp/webhook")
async def handle_webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        body = await request.json()
        logger.info(f"📨 Received webhook: {json.dumps(body, indent=2)}")
        
        # Process WhatsApp message
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        
                        # Process messages
                        for message in value.get("messages", []):
                            await process_whatsapp_message(message, value.get("metadata", {}))
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

async def process_whatsapp_message(message: dict, metadata: dict):
    """Process individual WhatsApp message"""
    try:
        from_phone = message.get("from")
        message_type = message.get("type")
        
        if message_type == "text":
            text_content = message.get("text", {}).get("body", "")
            await handle_text_message(from_phone, text_content)
        elif message_type == "interactive":
            interactive_content = message.get("interactive", {})
            await handle_interactive_message(from_phone, interactive_content)
            
    except Exception as e:
        logger.error(f"❌ Error processing message: {e}")

async def handle_text_message(phone: str, text: str):
    """Handle text messages"""
    try:
        logger.info(f"💬 Received text from {phone}: {text}")
        
        # Generate AI response
        if model:
            ai_result = ai_controller.generate_response(text, phone)
            if isinstance(ai_result, tuple):
                response, suggestions = ai_result
            else:
                response = ai_result
                suggestions = ["View Products", "Get Help", "Contact Support"]
        else:
            response = "Hello! I'm Isabi's AI assistant. How can I help you today?"
            suggestions = ["View Products", "Get Help", "Contact Support"]
        
        # Send interactive message with buttons
        await send_interactive_message(phone, response, suggestions)
        
    except Exception as e:
        logger.error(f"❌ Error handling text message: {e}")

async def handle_interactive_message(phone: str, interactive: dict):
    """Handle interactive messages (buttons, lists)"""
    try:
        logger.info(f"🔘 Received interactive message from {phone}")
        
        # Handle button responses
        if interactive.get("type") == "button_reply":
            button_text = interactive.get("button_reply", {}).get("title", "")
            await handle_text_message(phone, button_text)
            
    except Exception as e:
        logger.error(f"❌ Error handling interactive message: {e}")

async def send_whatsapp_message(phone: str, message: str):
    """Send WhatsApp message"""
    try:
        url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            logger.info(f"✅ Message sent to {phone}")
        else:
            logger.error(f"❌ Failed to send message: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp message: {e}")

# --------------------
# START SERVER
# --------------------
if __name__ == "__main__":
    # Check if products were loaded successfully
    if not PRODUCTS_DATABASE:
        logger.error("❌ ERROR: No products loaded from PostgreSQL database!")
        logger.error("Make sure your database connection is working and has product data.")
        exit(1)

    # Check WhatsApp token
    if not ACCESS_TOKEN or ACCESS_TOKEN == "YOUR_NEW_TOKEN_HERE":
        logger.error("❌ ERROR: Please update your WHATSAPP_TOKEN in the .env file!")
        logger.error("Go to Facebook Developers > Your App > WhatsApp > API Setup > Generate Token")
        exit(1)

    # Start server
    logger.info("🚀 Starting Enhanced Isabi WhatsApp Sales Bot with AI Control...")
    logger.info(f"🛍️ AI Seller Bot is active - Ready to sell {len(PRODUCTS_DATABASE)} digital products!")
    logger.info(f"📂 Categories available: {', '.join(PRODUCT_CATEGORIES)}")
    logger.info("📱 Interactive buttons and conversation flow enabled")
    logger.info("🗄️ Using PostgreSQL database for product data")
    logger.info("💾 Chat history storage enabled")
    logger.info("🎛️ AI Prompt Management System active")
    logger.info("🔍 GCP Vector Search integration active")
    if model is not None:
        logger.info("🤖 Gemini AI integration is active with controlled prompts")
    else:
        logger.info("⚠️ Gemini AI is not available - using fallback responses")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

async def send_interactive_message(phone: str, message: str, buttons: List[str]):
    """Send WhatsApp interactive message with buttons"""
    try:
        url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Create button objects (max 3 buttons)
        button_objects = []
        for i, button_text in enumerate(buttons[:3]):
            button_objects.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{i+1}",
                    "title": button_text
                }
            })
        
        data = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message
                },
                "action": {
                    "buttons": button_objects
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            logger.info(f"✅ Interactive message sent to {phone}")
        else:
            logger.error(f"❌ Failed to send interactive message: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error sending interactive message: {e}")
