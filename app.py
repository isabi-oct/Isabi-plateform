"""
Isabi WhatsApp Sales Bot - Agentic AI System
Main Application Entry Point

This is the main application file that orchestrates the entire Agentic AI system
for the WhatsApp sales bot with integrated payment processing and product management.
"""

import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the new agentic system
from Backend.core.agents.orchestrator import agent_orchestrator
from api.whatsapp.webhook import router as whatsapp_router
from api.payment.flutterwave import router as payment_router
from api.products.catalog import router as products_router
from api.health import router as health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting Isabi Agentic AI WhatsApp Sales Bot...")
    logger.info("🤖 Agentic AI System initialized")
    logger.info("📱 WhatsApp integration active")
    logger.info("💳 Payment processing ready")
    logger.info("🛍️ Product management active")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Isabi Agentic AI WhatsApp Sales Bot...")

# Create FastAPI application
app = FastAPI(
    title="Isabi Agentic AI WhatsApp Sales Bot",
    description="AI-powered WhatsApp sales bot with Agentic AI architecture",
    version="3.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(whatsapp_router, prefix="/api", tags=["WhatsApp"])
app.include_router(payment_router, prefix="/api/payment", tags=["Payment"])
app.include_router(products_router, prefix="/api/products", tags=["Products"])
app.include_router(health_router, prefix="/api", tags=["Health"])

@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": "Isabi Agentic AI WhatsApp Sales Bot",
        "version": "3.0.0",
        "status": "running",
        "architecture": "Agentic AI",
        "features": [
            "Multi-agent conversation system",
            "AI-powered product recommendations",
            "Intelligent sales process",
            "Automated payment processing",
            "WhatsApp integration",
            "PostgreSQL database",
            "GCP Vector Search",
            "Flutterwave payments"
        ],
        "agents": {
            "conversation": "Handles general conversation flow",
            "product": "Manages product discovery and recommendations",
            "sales": "Guides sales process and objection handling",
            "payment": "Processes payments and order management"
        }
    }

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents."""
    return agent_orchestrator.get_system_status()

@app.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get status of specific agent."""
    return agent_orchestrator.get_agent_status(agent_id)

@app.get("/conversations/{user_id}/status")
async def get_conversation_status(user_id: str):
    """Get status of user conversation."""
    return agent_orchestrator.get_conversation_status(user_id)

@app.post("/conversations/{user_id}/reset")
async def reset_conversation(user_id: str):
    """Reset conversation for a user."""
    agent_orchestrator.reset_conversation(user_id)
    return {"message": f"Conversation reset for user {user_id}"}

if __name__ == "__main__":
    # Environment checks
    required_env_vars = [
        "DATABASE_URL",
        "WHATSAPP_TOKEN", 
        "WHATSAPP_PHONE_NUMBER_ID",
        "GEMINI_API_KEY"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.error("Please check your .env file and ensure all required variables are set.")
        exit(1)
    
    # Start the server
    logger.info("🚀 Starting Isabi Agentic AI WhatsApp Sales Bot...")
    logger.info("🤖 Multi-agent system ready")
    logger.info("📱 WhatsApp webhook endpoints active")
    logger.info("💳 Payment processing enabled")
    logger.info("🛍️ Product catalog loaded")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
