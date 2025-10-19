"""
Flutterwave Payment Service

This service handles all Flutterwave payment operations including:
- Payment initialization
- Transaction verification
- Webhook processing
- Payment status tracking
- Refund processing

Author: AI Assistant
Created: 2025
"""

import os
import json
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from Backend.models.database.models import Order, OrderStatus
from Backend.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class FlutterwavePaymentService:
    """
    Flutterwave Payment Service for handling all payment operations.
    
    This service provides methods for:
    - Creating payment links
    - Processing payments
    - Verifying transactions
    - Handling webhooks
    - Managing refunds
    """
    
    def __init__(self):
        """Initialize Flutterwave payment service with configuration."""
        self.public_key = settings.flutterwave_public_key
        self.secret_key = settings.flutterwave_secret_key
        self.encryption_key = settings.flutterwave_encryption_key
        self.base_url = settings.flutterwave_base_url
        self.currency = settings.flutterwave_currency
        self.timeout = settings.flutterwave_timeout
        
        # Validate required configuration
        if not all([self.public_key, self.secret_key, self.encryption_key]):
            raise ValueError("Flutterwave configuration is incomplete. Please check your environment variables.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for Flutterwave API requests."""
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _generate_transaction_reference(self, order_id: int) -> str:
        """Generate a unique transaction reference for Flutterwave."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"ISABI_{order_id}_{timestamp}"
    
    def _encrypt_payload(self, payload: Dict[str, Any]) -> str:
        """
        Encrypt sensitive payload data using Flutterwave's encryption key.
        
        Args:
            payload: The data to encrypt
            
        Returns:
            Encrypted string
        """
        import base64
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        
        # Convert payload to JSON string
        json_payload = json.dumps(payload)
        
        # Create cipher
        key = self.encryption_key.encode('utf-8')
        cipher = AES.new(key, AES.MODE_CBC)
        
        # Encrypt the payload
        padded_data = pad(json_payload.encode('utf-8'), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Return base64 encoded encrypted data
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def create_payment_link(self, amount: float, product_name: str, order_id: int, 
                           customer_email: str, customer_name: str, customer_phone: str) -> Dict[str, Any]:
        """
        Create a Flutterwave payment link for the given order.
        
        Args:
            amount: Payment amount
            product_name: Name of the product being purchased
            order_id: Unique order identifier
            customer_email: Customer's email address
            customer_name: Customer's full name
            customer_phone: Customer's phone number
            
        Returns:
            Dictionary containing payment link details or error information
        """
        try:
            tx_ref = self._generate_transaction_reference(order_id)
            
            # Prepare payment data
            payment_data = {
                "tx_ref": tx_ref,
                "amount": str(amount),
                "currency": self.currency,
                "redirect_url": f"{settings.app_base_url}/payment/callback",
                "customer": {
                    "email": customer_email,
                    "name": customer_name,
                    "phone_number": customer_phone
                },
                "customizations": {
                    "title": "Isabi Platform Payment",
                    "description": f"Payment for {product_name}",
                    "logo": f"{settings.app_base_url}/static/logo.png"
                },
                "meta": {
                    "order_id": order_id,
                    "product_name": product_name
                }
            }
            
            # Make API request to Flutterwave
            response = requests.post(
                f"{self.base_url}/v3/payments",
                headers=self._get_headers(),
                json=payment_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("status") == "success":
                    payment_link = response_data["data"]["link"]
                    
                    return {
                        "success": True,
                        "payment_link": payment_link,
                        "transaction_reference": tx_ref,
                        "flutterwave_reference": response_data["data"]["reference"],
                        "expires_at": datetime.utcnow() + timedelta(minutes=settings.payment_link_expiry_minutes)
                    }
                else:
                    logger.error(f"Flutterwave payment creation failed: {response_data}")
                    return {
                        "success": False,
                        "error": response_data.get("message", "Payment creation failed")
                    }
            else:
                logger.error(f"Flutterwave API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API request failed with status {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error creating payment link: {str(e)}")
            return {
                "success": False,
                "error": "Network error occurred while creating payment link"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating payment link: {str(e)}")
            return {
                "success": False,
                "error": "An unexpected error occurred"
            }
    
    def verify_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify a Flutterwave transaction using the transaction ID.
        
        Args:
            transaction_id: Flutterwave transaction ID
            
        Returns:
            Dictionary containing transaction verification details
        """
        try:
            response = requests.get(
                f"{self.base_url}/v3/transactions/{transaction_id}/verify",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("status") == "success":
                    transaction_data = response_data["data"]
                    
                    return {
                        "success": True,
                        "transaction_id": transaction_data["id"],
                        "status": transaction_data["status"],
                        "amount": transaction_data["amount"],
                        "currency": transaction_data["currency"],
                        "customer_email": transaction_data["customer"]["email"],
                        "payment_type": transaction_data["payment_type"],
                        "created_at": transaction_data["created_at"],
                        "tx_ref": transaction_data["tx_ref"]
                    }
                else:
                    logger.error(f"Transaction verification failed: {response_data}")
                    return {
                        "success": False,
                        "error": response_data.get("message", "Transaction verification failed")
                    }
            else:
                logger.error(f"Flutterwave verification API error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Verification request failed with status {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error verifying transaction: {str(e)}")
            return {
                "success": False,
                "error": "Network error occurred while verifying transaction"
            }
        except Exception as e:
            logger.error(f"Unexpected error verifying transaction: {str(e)}")
            return {
                "success": False,
                "error": "An unexpected error occurred during verification"
            }
    
    def process_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """
        Process Flutterwave webhook notifications.
        
        Args:
            payload: Webhook payload data
            signature: Webhook signature for verification
            
        Returns:
            Dictionary containing webhook processing result
        """
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(payload, signature):
                logger.warning("Invalid webhook signature received")
                return {
                    "success": False,
                    "error": "Invalid webhook signature"
                }
            
            event_type = payload.get("event")
            data = payload.get("data", {})
            
            if event_type == "charge.completed":
                return self._handle_payment_completed(data)
            elif event_type == "charge.failed":
                return self._handle_payment_failed(data)
            elif event_type == "transfer.completed":
                return self._handle_transfer_completed(data)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
                return {
                    "success": True,
                    "message": f"Event {event_type} received but not processed"
                }
                
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {
                "success": False,
                "error": "Error processing webhook"
            }
    
    def _verify_webhook_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify Flutterwave webhook signature.
        
        Args:
            payload: Webhook payload
            signature: Webhook signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Create expected signature
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                json.dumps(payload, separators=(',', ':')).encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    def _handle_payment_completed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment completed webhook event."""
        try:
            tx_ref = data.get("tx_ref")
            transaction_id = data.get("id")
            status = data.get("status")
            
            if status == "successful":
                # Update order status in database
                # This would typically involve database operations
                logger.info(f"Payment completed successfully for transaction {transaction_id}")
                
                return {
                    "success": True,
                    "message": "Payment completed successfully",
                    "transaction_id": transaction_id,
                    "tx_ref": tx_ref
                }
            else:
                logger.warning(f"Payment not successful for transaction {transaction_id}: {status}")
                return {
                    "success": False,
                    "message": f"Payment status: {status}",
                    "transaction_id": transaction_id
                }
                
        except Exception as e:
            logger.error(f"Error handling payment completed: {str(e)}")
            return {
                "success": False,
                "error": "Error processing payment completion"
            }
    
    def _handle_payment_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment failed webhook event."""
        try:
            tx_ref = data.get("tx_ref")
            transaction_id = data.get("id")
            
            logger.warning(f"Payment failed for transaction {transaction_id}")
            
            return {
                "success": True,
                "message": "Payment failed event processed",
                "transaction_id": transaction_id,
                "tx_ref": tx_ref
            }
            
        except Exception as e:
            logger.error(f"Error handling payment failed: {str(e)}")
            return {
                "success": False,
                "error": "Error processing payment failure"
            }
    
    def _handle_transfer_completed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transfer completed webhook event."""
        try:
            transfer_id = data.get("id")
            status = data.get("status")
            
            logger.info(f"Transfer {transfer_id} completed with status: {status}")
            
            return {
                "success": True,
                "message": "Transfer completed event processed",
                "transfer_id": transfer_id,
                "status": status
            }
            
        except Exception as e:
            logger.error(f"Error handling transfer completed: {str(e)}")
            return {
                "success": False,
                "error": "Error processing transfer completion"
            }
    
    def initiate_refund(self, transaction_id: str, amount: Optional[float] = None, 
                        reason: str = "Customer request") -> Dict[str, Any]:
        """
        Initiate a refund for a Flutterwave transaction.
        
        Args:
            transaction_id: Flutterwave transaction ID
            amount: Refund amount (if None, full refund)
            reason: Reason for refund
            
        Returns:
            Dictionary containing refund initiation result
        """
        try:
            refund_data = {
                "tx_ref": transaction_id,
                "amount": str(amount) if amount else None,
                "reason": reason
            }
            
            response = requests.post(
                f"{self.base_url}/v3/refunds",
                headers=self._get_headers(),
                json=refund_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("status") == "success":
                    return {
                        "success": True,
                        "refund_id": response_data["data"]["id"],
                        "status": response_data["data"]["status"],
                        "amount": response_data["data"]["amount"]
                    }
                else:
                    logger.error(f"Refund initiation failed: {response_data}")
                    return {
                        "success": False,
                        "error": response_data.get("message", "Refund initiation failed")
                    }
            else:
                logger.error(f"Flutterwave refund API error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Refund request failed with status {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error initiating refund: {str(e)}")
            return {
                "success": False,
                "error": "Network error occurred while initiating refund"
            }
        except Exception as e:
            logger.error(f"Unexpected error initiating refund: {str(e)}")
            return {
                "success": False,
                "error": "An unexpected error occurred during refund initiation"
            }
    
    def get_transaction_history(self, customer_email: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get transaction history for a customer.
        
        Args:
            customer_email: Customer's email address
            limit: Maximum number of transactions to return
            
        Returns:
            Dictionary containing transaction history
        """
        try:
            params = {
                "customer_email": customer_email,
                "limit": limit
            }
            
            response = requests.get(
                f"{self.base_url}/v3/transactions",
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("status") == "success":
                    return {
                        "success": True,
                        "transactions": response_data["data"],
                        "total": len(response_data["data"])
                    }
                else:
                    logger.error(f"Transaction history retrieval failed: {response_data}")
                    return {
                        "success": False,
                        "error": response_data.get("message", "Failed to retrieve transaction history")
                    }
            else:
                logger.error(f"Flutterwave history API error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"History request failed with status {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error retrieving transaction history: {str(e)}")
            return {
                "success": False,
                "error": "Network error occurred while retrieving transaction history"
            }
        except Exception as e:
            logger.error(f"Unexpected error retrieving transaction history: {str(e)}")
            return {
                "success": False,
                "error": "An unexpected error occurred while retrieving transaction history"
            }

# Global instance
payment_service = FlutterwavePaymentService()
