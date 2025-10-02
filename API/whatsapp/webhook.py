# Enhanced WhatsApp Webhook with Database Integration and Suggestion Buttons
from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import Response
import json
import logging
from Backend.services.ai_conversation import ai_conversation_service
from Backend.services.whatsapp_service import whatsapp_service

router = APIRouter(tags=["WhatsApp"])
logger = logging.getLogger(__name__)

@router.get("/whatsapp/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Verify WhatsApp webhook"""
    VERIFY_TOKEN = "user-product"  # Should come from config
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        return Response(content=hub_challenge, media_type="text/plain")
    
    logger.error("❌ Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp/webhook")
async def handle_webhook(request: Request):
    """Handle incoming WhatsApp messages with enhanced AI and suggestions"""
    try:
        body = await request.json()
        logger.info(f"📱 Received enhanced webhook: {json.dumps(body, indent=2)}")
        
        # Process the webhook data
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        await process_message_with_enhanced_ai(change.get("value", {}))
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_message_with_enhanced_ai(value):
    """Process incoming WhatsApp message with enhanced AI and database integration"""
    for message_data in value.get("messages", []):
        user_id = message_data.get("from")
        message_text = message_data.get("text", {}).get("body")
        
        if user_id and message_text:
            logger.info(f"📱 Message from {user_id}: {message_text}")
            
            # Process message with enhanced AI (includes database products)
            ai_response = await ai_conversation_service.process_message(
                message=message_text,
                user_id=user_id,
                context={"conversation_type": "whatsapp"}
            )
            
            # Extract response components
            response_text = ai_response.get("text", "Sorry, I couldn't process your message.")
            suggestions = ai_response.get("suggestions", [])
            products = ai_response.get("products", [])
            
            # Send response with suggestions
            await whatsapp_service.send_message(
                to=user_id,
                message=response_text,
                suggestions=suggestions
            )
            
            logger.info(f"🤖 Enhanced AI response sent to {user_id}: {response_text}")
            logger.info(f"🔘 Suggestions sent: {suggestions}")
            
        else:
            logger.warning(f"Invalid message data received: {message_data}")

@router.post("/test-ai")
async def test_ai_conversation_endpoint(message: str, phone_number: str):
    """Test enhanced AI conversation directly via API"""
    try:
        # Process message with enhanced AI
        ai_response = await ai_conversation_service.process_message(
            message=message,
            user_id=phone_number,
            context={"conversation_type": "test"}
        )
        
        # Extract response components
        response_text = ai_response.get("text", "Sorry, I couldn't process your message.")
        suggestions = ai_response.get("suggestions", [])
        products = ai_response.get("products", [])
        
        # Send response with suggestions
        await whatsapp_service.send_message(
            to=phone_number,
            message=response_text,
            suggestions=suggestions
        )
        
        return {
            "status": "success",
            "ai_response": {
                "text": response_text,
                "suggestions": suggestions,
                "products": products
            }
        }
    except Exception as e:
        logger.error(f"Error testing enhanced AI conversation: {e}")
        raise HTTPException(status_code=500, detail="Enhanced AI test failed")
