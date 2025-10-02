# WhatsApp Message Sender
import requests
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class MessageSender:
    def __init__(self):
        self.whatsapp_token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
    
    async def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a text message via WhatsApp API"""
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
            logger.info(f"Message sent successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def send_template_message(self, to: str, template_name: str, parameters: list) -> Dict[str, Any]:
        """Send a template message via WhatsApp API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [{"type": "text", "text": param} for param in parameters]
                        }
                    ]
                }
            }
            
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Template message sent successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending template message: {e}")
            raise
    
    async def send_interactive_message(self, to: str, header_text: str, body_text: str, buttons: list) -> Dict[str, Any]:
        """Send an interactive message with buttons"""
        try:
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "header": {"type": "text", "text": header_text},
                    "body": {"text": body_text},
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {"id": f"btn_{i}", "title": button}
                            }
                            for i, button in enumerate(buttons)
                        ]
                    }
                }
            }
            
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Interactive message sent successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending interactive message: {e}")
            raise
