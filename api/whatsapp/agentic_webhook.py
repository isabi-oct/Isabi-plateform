"""
Agentic WhatsApp Webhook

This module provides WhatsApp webhook endpoints that integrate with the
new Agentic AI system for autonomous reasoning and tool execution.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from src.agents.core_agent import CoreAgent, AgentContext
from Backend.services.whatsapp_service import whatsapp_service
from Backend.models.database.database import get_db
from Backend.models.database.models import User, ChatSession

logger = logging.getLogger(__name__)

# Initialize the core agent
core_agent = CoreAgent()

# Create router
router = APIRouter(tags=["Agentic WhatsApp"])

class TestMessageRequest(BaseModel):
    message: str
    phone_number: str

@router.get("/whatsapp/agentic/webhook")
async def verify_agentic_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Verify WhatsApp webhook for agentic system."""
    VERIFY_TOKEN = "agentic-product"  # Should come from config
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✅ Agentic WhatsApp webhook verified successfully")
        return Response(content=hub_challenge, media_type="text/plain")
    
    logger.error("❌ Agentic WhatsApp webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp/agentic/webhook")
async def handle_agentic_webhook(request: Request):
    """Handle incoming WhatsApp messages with Agentic AI system."""
    try:
        body = await request.json()
        logger.info(f"📱 Received agentic WhatsApp webhook: {json.dumps(body, indent=2)}")
        
        # Process the webhook data
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        await process_message_with_agentic_ai(change.get("value", {}))
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"❌ Error processing agentic WhatsApp webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_message_with_agentic_ai(value: Dict[str, Any]):
    """Process incoming WhatsApp message with Agentic AI system."""
    try:
        for message_data in value.get("messages", []):
            user_id = message_data.get("from")
            message_text = message_data.get("text", {}).get("body")
            
            if user_id and message_text:
                logger.info(f"📱 Processing agentic message from {user_id}: {message_text}")
                
                # Get or create user
                user = await get_or_create_user(user_id)
                
                # Get conversation history
                conversation_history = await get_conversation_history(user.id)
                
                # Create agent context
                context = AgentContext(
                    user_id=user_id,
                    message=message_text,
                    conversation_history=conversation_history,
                    user_profile=user,
                    platform="whatsapp",
                    timestamp=datetime.now()
                )
                
                # Process message through Agentic AI system
                ai_response = await core_agent.process_message(context)
                
                # Extract response components
                response_text = ai_response.get("response", "Sorry, I couldn't process your message.")
                actions = ai_response.get("actions", [])
                metadata = ai_response.get("metadata", {})
                
                # Send response via WhatsApp
                await whatsapp_service.send_message(
                    to=user_id,
                    message=response_text
                )
                
                # Log the interaction
                logger.info(f"🤖 Agentic AI response sent to {user_id}")
                logger.info(f"🔧 Actions taken: {len(actions)}")
                logger.info(f"📊 Metadata: {metadata}")
                
                # Handle specific actions
                await handle_agent_actions(actions, user_id, user.id)
                
            else:
                logger.warning(f"Invalid message data received: {message_data}")
                
    except Exception as e:
        logger.error(f"❌ Error processing message with Agentic AI: {e}")

async def get_or_create_user(phone_number: str) -> User:
    """Get or create user by phone number."""
    try:
        db = next(get_db())
        user = db.query(User).filter(User.phone_number == phone_number).first()
        
        if not user:
            user = User(
                phone_number=phone_number,
                name=f"User_{phone_number[-4:]}",
                status="active"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {user.id}")
        
        return user
        
    except Exception as e:
        logger.error(f"Error getting/creating user: {e}")
        raise

async def get_conversation_history(user_id: int) -> List[Dict[str, Any]]:
    """Get conversation history for user."""
    try:
        db = next(get_db())
        session = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        ).first()
        
        if session and session.session_data:
            return session.session_data.get("conversation_history", [])
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []

async def handle_agent_actions(actions: List[Dict[str, Any]], phone_number: str, user_id: int):
    """Handle specific actions taken by the agent."""
    try:
        for action in actions:
            action_type = action.get("type")
            
            if action_type == "tool_call":
                tool_name = action.get("tool")
                tool_input = action.get("input", {})
                tool_result = action.get("result", {})
                
                logger.info(f"🔧 Agent used tool: {tool_name}")
                
                # Handle specific tool results
                if tool_name == "create_payment_link" and tool_result.get("success"):
                    payment_link = tool_result.get("payment_link")
                    if payment_link:
                        # Send payment link via WhatsApp
                        await whatsapp_service.send_message(
                            to=phone_number,
                            message=f"💳 Here's your payment link: {payment_link}\n\nClick to complete your purchase!"
                        )
                
                elif tool_name == "verify_transaction" and tool_result.get("success"):
                    status = tool_result.get("status")
                    if status == "successful":
                        await whatsapp_service.send_message(
                            to=phone_number,
                            message="✅ Payment successful! Your order has been confirmed. You'll receive your product details shortly."
                        )
                    elif status == "failed":
                        await whatsapp_service.send_message(
                            to=phone_number,
                            message="❌ Payment failed. Please try again or contact support if the issue persists."
                        )
                
                elif tool_name == "start_tutoring_session" and tool_result.get("success"):
                    await whatsapp_service.send_message(
                        to=phone_number,
                        message="🎓 Tutoring session started! I'm now your AI tutor. Ask me any questions about your product!"
                    )
                
                elif tool_name == "search_ai_questions" and tool_result.get("success"):
                    results = tool_result.get("results", [])
                    if results:
                        # Send top relevant Q&A
                        top_result = results[0]
                        await whatsapp_service.send_message(
                            to=phone_number,
                            message=f"❓ **Q:** {top_result.get('question', '')}\n\n💡 **A:** {top_result.get('answer', '')}"
                        )
                
                elif tool_name == "get_product_recommendations" and tool_result.get("success"):
                    recommendations = tool_result.get("recommendations", [])
                    if recommendations:
                        message = "🛍️ **Recommended products for you:**\n\n"
                        for i, rec in enumerate(recommendations[:3], 1):
                            product = rec.get("product", {})
                            message += f"{i}. **{product.get('name', '')}** - ${product.get('price', 0)}\n"
                            message += f"   {product.get('description', '')[:100]}...\n\n"
                        
                        await whatsapp_service.send_message(
                            to=phone_number,
                            message=message
                        )
        
    except Exception as e:
        logger.error(f"Error handling agent actions: {e}")

@router.post("/whatsapp/agentic/test")
async def test_agentic_conversation(request: TestMessageRequest):
    """Test Agentic AI conversation directly via API."""
    try:
        logger.info(f"🧪 Testing agentic conversation: {request.message}")
        
        # Get or create user
        user = await get_or_create_user(request.phone_number)
        
        # Get conversation history
        conversation_history = await get_conversation_history(user.id)
        
        # Create agent context
        context = AgentContext(
            user_id=request.phone_number,
            message=request.message,
            conversation_history=conversation_history,
            user_profile=user,
            platform="test",
            timestamp=datetime.now()
        )
        
        # Process message through Agentic AI system
        ai_response = await core_agent.process_message(context)
        
        # Extract response components
        response_text = ai_response.get("response", "Sorry, I couldn't process your message.")
        actions = ai_response.get("actions", [])
        metadata = ai_response.get("metadata", {})
        
        return {
            "status": "success",
            "agentic_response": {
                "response": response_text,
                "actions": actions,
                "metadata": metadata
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error testing agentic conversation: {e}")
        raise HTTPException(status_code=500, detail="Agentic AI test failed")

@router.get("/whatsapp/agentic/status")
async def get_agentic_status():
    """Get status of the agentic AI system."""
    try:
        agent_status = core_agent.get_agent_status()
        
        return {
            "status": "success",
            "agentic_system": agent_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agentic status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agentic status")

@router.post("/whatsapp/agentic/reset/{phone_number}")
async def reset_agentic_conversation(phone_number: str):
    """Reset conversation for a user."""
    try:
        core_agent.reset_conversation(phone_number)
        
        return {
            "status": "success",
            "message": f"Conversation reset for {phone_number}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset conversation")

@router.get("/whatsapp/agentic/analytics")
async def get_agentic_analytics():
    """Get analytics for the agentic AI system."""
    try:
        # Get basic system metrics
        agent_status = core_agent.get_agent_status()
        
        # Get database metrics
        db = next(get_db())
        total_users = db.query(User).count()
        active_sessions = db.query(ChatSession).filter(ChatSession.is_active == True).count()
        
        return {
            "status": "success",
            "analytics": {
                "agent_system": agent_status,
                "users": {
                    "total_users": total_users,
                    "active_sessions": active_sessions
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting agentic analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")
