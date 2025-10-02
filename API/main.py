# Main API Router
from fastapi import FastAPI, APIRouter
import logging

# Import routers from their respective __init__.py files
from API.whatsapp import webhook_router, message_router
from API.payment import orange_money_router
from API.products import catalog_router
from API.admin import admin_router

app = FastAPI(
    title="Enhanced Isabi WhatsApp Sales Bot API",
    version="2.1.0",
    description="Enhanced API for Isabi WhatsApp Sales Bot with database integration and suggestion buttons."
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Enhanced Isabi WhatsApp Sales Bot API",
        "version": "2.1.0",
        "status": "running",
        "features": [
            "Enhanced WhatsApp Integration with Database",
            "AI-Powered Product Recommendations",
            "Interactive Suggestion Buttons",
            "Orange Money Payments",
            "Product Management",
            "Admin Panel"
        ],
        "endpoints": {
            "whatsapp": "/whatsapp",
            "payment": "/payment/orange-money",
            "products": "/products",
            "admin": "/admin"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "enhanced-isabi-bot-api",
        "version": "2.1.0",
        "features": ["database_integration", "suggestion_buttons", "product_recommendations"]
    }

# Include routers
app.include_router(webhook_router, prefix="/whatsapp", tags=["WhatsApp"])
app.include_router(message_router, prefix="/whatsapp", tags=["WhatsApp"])
app.include_router(orange_money_router, prefix="/payment/orange-money", tags=["Payment"])
app.include_router(catalog_router, prefix="/products", tags=["Products"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
