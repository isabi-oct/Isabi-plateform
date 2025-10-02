# Enhanced WhatsApp Service with Interactive Messages
import os
import requests
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        """Initialize enhanced WhatsApp service"""
        self.whatsapp_token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.api_version = "v18.0"
        
        if self.whatsapp_token and self.phone_number_id:
            self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
            logger.info("📱 Enhanced WhatsApp service initialized")
        else:
            logger.warning("⚠️ WhatsApp credentials not found - using mock mode")
            self.base_url = None
    
    async def send_message(self, to: str, message: str, suggestions: List[str] = None) -> Dict[str, Any]:
        """Send message via WhatsApp API with optional suggestions"""
        try:
            logger.info(f"📤 Sending WhatsApp message to {to}: {message}")
            
            if self.base_url and self.whatsapp_token and suggestions:
                # Send interactive message with buttons
                return await self._send_interactive_message(to, message, suggestions)
            elif self.base_url and self.whatsapp_token:
                # Send regular text message
                return await self._send_text_message(to, message)
            else:
                # Mock response for testing
                return await self._send_mock_message(to, message, suggestions)
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def _send_interactive_message(self, to: str, message: str, suggestions: List[str]) -> Dict[str, Any]:
        """Send interactive message with buttons"""
        try:
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json"
            }
            
            # Create buttons from suggestions
            buttons = []
            for i, suggestion in enumerate(suggestions[:3]):  # WhatsApp allows max 3 buttons
                buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": f"btn_{i+1}",
                        "title": suggestion[:20]  # WhatsApp button title limit
                    }
                })
            
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": message
                    },
                    "action": {
                        "buttons": buttons
                    }
                }
            }
            
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Interactive WhatsApp message sent successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending interactive message: {e}")
            # Fallback to text message
            return await self._send_text_message(to, message)
    
    async def _send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send regular text message"""
        try:
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ WhatsApp text message sent successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending text message: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def _send_mock_message(self, to: str, message: str, suggestions: List[str] = None) -> Dict[str, Any]:
        """Send mock message for testing"""
        if suggestions:
            logger.info(f"🧪 MOCK: Would send interactive message to {to}: {message}")
            logger.info(f"🧪 MOCK: Buttons: {suggestions}")
        else:
            logger.info(f"🧪 MOCK: Would send to {to}: {message}")
        
        return {
            "messaging_product": "whatsapp",
            "contacts": [{"input": to, "wa_id": to}],
            "messages": [{"id": "mock_message_id", "message_status": "accepted"}],
            "status": "mock_success"
        }

# Create global instance
whatsapp_service = WhatsAppService()
