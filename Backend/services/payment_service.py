import requests
from datetime import datetime, timedelta
from app.config.settings import settings
from typing import Dict, Any, Optional
import json

class PaymentService:
    def __init__(self):
        self.merchant_id = settings.orange_money_merchant_id
        self.merchant_key = settings.orange_money_merchant_key
        self.base_url = settings.orange_money_base_url
        self.currency = settings.orange_money_currency
    
    def create_payment_link(self, amount: float, product_name: str, order_id: int) -> Dict[str, Any]:
        """Create an Orange Money payment link with 5-minute expiry"""
        try:
            # For now, return a mock payment link
            # In production, you would integrate with Orange Money API
            payment_link = f"https://payment.example.com/pay/{order_id}?amount={amount}&product={product_name}"
            
            return {
                "success": True,
                "payment_link": payment_link,
                "expires_at": datetime.utcnow() + timedelta(minutes=settings.payment_link_expiry_minutes)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verify if payment was successful"""
        try:
            # For now, return a mock verification
            # In production, you would check with Orange Money API
            return {
                "success": True,
                "status": "succeeded",
                "amount": 0.0,
                "paid": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """Handle Orange Money webhook events"""
        try:
            # For now, return a mock webhook handler
            # In production, you would verify the signature and process the webhook
            return {
                "success": True,
                "event_type": "payment_succeeded",
                "payment_id": "mock_payment_id",
                "amount": 0.0,
                "metadata": {}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global instance
payment_service = PaymentService()
