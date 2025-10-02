# Orange Money Payment Processor
import requests
import logging
from typing import Dict, Any, Optional
import os
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class PaymentProcessor:
    def __init__(self):
        self.merchant_id = os.getenv("ORANGE_MONEY_MERCHANT_ID")
        self.merchant_key = os.getenv("ORANGE_MONEY_MERCHANT_KEY")
        self.base_url = os.getenv("ORANGE_MONEY_BASE_URL", "https://api.orange.com/orange-money-webpay/cm/v1")
        self.currency = "XAF"
    
    async def initiate_payment(self, amount: float, phone_number: str, description: str, order_id: str) -> Dict[str, Any]:
        """Initiate Orange Money payment"""
        try:
            transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
            
            headers = {
                "Authorization": f"Bearer {self.merchant_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "merchant_id": self.merchant_id,
                "amount": amount,
                "currency": self.currency,
                "phone_number": phone_number,
                "description": description,
                "order_id": order_id,
                "transaction_id": transaction_id,
                "callback_url": "https://your-domain.com/payment/callback"
            }
            
            response = requests.post(f"{self.base_url}/payments", headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Payment initiated successfully: {result}")
            
            return {
                "transaction_id": transaction_id,
                "status": "pending",
                "payment_url": result.get("payment_url"),
                "amount": amount,
                "currency": self.currency,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error initiating payment: {e}")
            raise
    
    async def check_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Check payment status"""
        try:
            headers = {
                "Authorization": f"Bearer {self.merchant_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(f"{self.base_url}/payments/{transaction_id}/status", headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Payment status checked: {result}")
            
            return {
                "transaction_id": transaction_id,
                "status": result.get("status", "unknown"),
                "amount": result.get("amount"),
                "currency": result.get("currency"),
                "timestamp": result.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            raise
    
    async def process_refund(self, transaction_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Process payment refund"""
        try:
            refund_id = f"ref_{uuid.uuid4().hex[:12]}"
            
            headers = {
                "Authorization": f"Bearer {self.merchant_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "transaction_id": transaction_id,
                "refund_id": refund_id,
                "amount": amount,
                "reason": "Customer request"
            }
            
            response = requests.post(f"{self.base_url}/refunds", headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Refund processed successfully: {result}")
            
            return {
                "refund_id": refund_id,
                "transaction_id": transaction_id,
                "status": "refunded",
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            raise
