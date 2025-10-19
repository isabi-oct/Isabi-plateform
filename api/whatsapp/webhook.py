"""
WhatsApp Webhook with Agentic AI Integration

This module provides WhatsApp webhook endpoints that integrate with the
Agentic AI system for intelligent conversation handling.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import Response
import json
import logging
from typing import Dict, Any

from Backend.core.agents.orchestrator import agent_orchestrator
from Backend.services.whatsapp_service import whatsapp_service

router = APIRouter(tags=["WhatsApp"])
logger = logging.getLogger(__name__)

@router.get("/whatsapp/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Verify WhatsApp webhook."""
    VERIFY_TOKEN = "user-product"  # Should come from config
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✅ WhatsApp webhook verified successfully")
        return Response(content=hub_challenge, media_type="text/plain")
    
    logger.error("❌ WhatsApp webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp/webhook")
async def handle_webhook(request: Request):
    """Handle incoming WhatsApp messages with Agentic AI system."""
    try:
        body = await request.json()
        logger.info(f"📱 Received WhatsApp webhook: {json.dumps(body, indent=2)}")
        
        # Process the webhook data
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        await process_message_with_agentic_ai(change.get("value", {}))
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"❌ Error processing WhatsApp webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_message_with_agentic_ai(value: Dict[str, Any]):
    """Process incoming WhatsApp message with Agentic AI system."""
    try:
        for message_data in value.get("messages", []):
            user_id = message_data.get("from")
            message_text = message_data.get("text", {}).get("body")
            
            if user_id and message_text:
                logger.info(f"📱 Processing message from {user_id}: {message_text}")
                
                # Process message through Agentic AI system
                ai_response = await agent_orchestrator.process_message(
                    user_id=user_id,
                    message=message_text,
                    context={
                        "conversation_type": "whatsapp",
                        "platform": "whatsapp",
                        "timestamp": message_data.get("timestamp")
                    }
                )
                
                # Extract response components
                response_text = ai_response.get("response", "Sorry, I couldn't process your message.")
                suggestions = ai_response.get("suggestions", [])
                products = ai_response.get("products", [])
                payment_link = ai_response.get("payment_link")
                
                # Send response with suggestions
                await whatsapp_service.send_message(
                    to=user_id,
                    message=response_text,
                    suggestions=suggestions
                )
                
                # Log the interaction
                logger.info(f"🤖 Agentic AI response sent to {user_id}")
                logger.info(f"🔘 Suggestions: {suggestions}")
                logger.info(f"🛍️ Products found: {len(products)}")
                if payment_link:
                    logger.info(f"💳 Payment link generated")
                
            else:
                logger.warning(f"Invalid message data received: {message_data}")
                
    except Exception as e:
        logger.error(f"❌ Error processing message with Agentic AI: {e}")

@router.post("/whatsapp/test-agentic")
async def test_agentic_conversation(message: str, phone_number: str):
    """Test Agentic AI conversation directly via API."""
    try:
        logger.info(f"🧪 Testing Agentic AI conversation: {message}")
        
        # Process message through Agentic AI system
        ai_response = await agent_orchestrator.process_message(
            user_id=phone_number,
            message=message,
            context={"conversation_type": "test"}
        )
        
        # Extract response components
        response_text = ai_response.get("response", "Sorry, I couldn't process your message.")
        suggestions = ai_response.get("suggestions", [])
        products = ai_response.get("products", [])
        payment_link = ai_response.get("payment_link")
        
        # Send response with suggestions
        await whatsapp_service.send_message(
            to=phone_number,
            message=response_text,
            suggestions=suggestions
        )
        
        return {
            "status": "success",
            "agentic_response": {
                "response": response_text,
                "suggestions": suggestions,
                "products": products,
                "payment_link": payment_link,
                "metadata": ai_response.get("metadata", {})
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error testing Agentic AI conversation: {e}")
        raise HTTPException(status_code=500, detail="Agentic AI test failed")

@router.get("/whatsapp/agents/status")
async def get_whatsapp_agents_status():
    """Get status of all agents in the WhatsApp context."""
    return agent_orchestrator.get_system_status()

@router.get("/whatsapp/conversations/{user_id}")
async def get_user_conversation(user_id: str):
    """Get user conversation status and history."""
    return agent_orchestrator.get_conversation_status(user_id)

@router.post("/whatsapp/conversations/{user_id}/reset")
async def reset_user_conversation(user_id: str):
    """Reset user conversation."""
    agent_orchestrator.reset_conversation(user_id)
    return {"message": f"Conversation reset for user {user_id}"}