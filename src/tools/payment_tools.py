"""
Payment Tools for Agentic AI System

This module provides tools for payment processing via Flutterwave API.
These tools allow the agent to handle payments autonomously.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field, EmailStr

from Backend.services.payment_service import payment_service
from Backend.models.database.database import get_db
from Backend.models.database.models import Order, OrderStatus

logger = logging.getLogger(__name__)

# Pydantic models for tool inputs
class CreatePaymentLinkInput(BaseModel):
    order_id: int = Field(..., description="Order ID to create payment for")
    customer_email: EmailStr = Field(..., description="Customer email address")
    customer_name: str = Field(..., description="Customer full name")
    customer_phone: str = Field(..., description="Customer phone number")

class VerifyTransactionInput(BaseModel):
    transaction_id: str = Field(..., description="Flutterwave transaction ID to verify")

class InitiateRefundInput(BaseModel):
    transaction_id: str = Field(..., description="Flutterwave transaction ID to refund")
    amount: Optional[float] = Field(None, description="Refund amount (if None, full refund)")
    reason: str = Field("Customer request", description="Reason for refund")

class GetTransactionHistoryInput(BaseModel):
    customer_email: EmailStr = Field(..., description="Customer email address")
    limit: int = Field(10, description="Maximum number of transactions to return")

class GetPaymentStatusInput(BaseModel):
    transaction_id: str = Field(..., description="Transaction ID to check status for")

class PaymentTools:
    """Payment tools for agentic AI system."""
    
    # Constants
    ORDER_NOT_FOUND = "Order not found"
    TRANSACTION_NOT_FOUND = "Transaction not found"
    
    def __init__(self):
        self.payment_service = payment_service
        logger.info("Payment tools initialized")
    
    def get_tools(self) -> List[BaseTool]:
        """Get all payment tools."""
        return [
            self.create_payment_link,
            self.verify_transaction,
            self.initiate_refund,
            self.get_transaction_history,
            self.get_payment_status,
            self.check_order_payment_status,
            self.update_order_payment_info
        ]
    
    @tool("create_payment_link", args_schema=CreatePaymentLinkInput)
    def create_payment_link(self, order_id: int, customer_email: str, 
                           customer_name: str, customer_phone: str) -> Dict[str, Any]:
        """Create a Flutterwave payment link for an order."""
        try:
            # Get order details from database
            db = next(get_db())
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                return {"success": False, "error": self.ORDER_NOT_FOUND}
            
            if order.status != OrderStatus.PENDING:
                return {"success": False, "error": f"Order is not in pending status (current: {order.status})"}
            
            # Get product details
            product = order.product
            if not product:
                return {"success": False, "error": "Product not found for order"}
            
            # Create payment link
            result = self.payment_service.create_payment_link(
                amount=order.amount,
                product_name=product.name,
                order_id=order_id,
                customer_email=customer_email,
                customer_name=customer_name,
                customer_phone=customer_phone
            )
            
            if result["success"]:
                # Update order with payment details
                order.payment_link = result["payment_link"]
                order.payment_link_expires_at = result["expires_at"]
                order.flutterwave_payment_id = result["flutterwave_reference"]
                order.flutterwave_transaction_id = result["transaction_reference"]
                db.commit()
                
                logger.info(f"Created payment link for order {order_id}")
                return {
                    "success": True,
                    "payment_link": result["payment_link"],
                    "transaction_reference": result["transaction_reference"],
                    "flutterwave_reference": result["flutterwave_reference"],
                    "expires_at": result["expires_at"].isoformat(),
                    "order_id": order_id
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Error creating payment link: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("verify_transaction", args_schema=VerifyTransactionInput)
    def verify_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Verify a Flutterwave transaction."""
        try:
            result = self.payment_service.verify_transaction(transaction_id)
            
            if result["success"]:
                # Update order status if payment is successful
                if result["status"] == "successful":
                    db = next(get_db())
                    order = db.query(Order).filter(
                        Order.flutterwave_transaction_id == result["tx_ref"]
                    ).first()
                    
                    if order:
                        order.status = OrderStatus.PAID
                        order.flutterwave_transaction_id = result["transaction_id"]
                        db.commit()
                        logger.info(f"Order {order.id} marked as paid")
                
                return {
                    "success": True,
                    "transaction_id": result["transaction_id"],
                    "status": result["status"],
                    "amount": result["amount"],
                    "currency": result["currency"],
                    "customer_email": result["customer_email"],
                    "payment_type": result["payment_type"],
                    "created_at": result["created_at"],
                    "tx_ref": result["tx_ref"]
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Error verifying transaction: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("initiate_refund", args_schema=InitiateRefundInput)
    def initiate_refund(self, transaction_id: str, amount: Optional[float] = None, 
                       reason: str = "Customer request") -> Dict[str, Any]:
        """Initiate a refund for a Flutterwave transaction."""
        try:
            # Verify transaction exists in our database
            db = next(get_db())
            order = db.query(Order).filter(
                Order.flutterwave_transaction_id == transaction_id
            ).first()
            
            if not order:
                return {"success": False, "error": "Transaction not found in our system"}
            
            if order.status != OrderStatus.PAID:
                return {"success": False, "error": "Cannot refund unpaid order"}
            
            # Initiate refund
            result = self.payment_service.initiate_refund(
                transaction_id=transaction_id,
                amount=amount,
                reason=reason
            )
            
            if result["success"]:
                # Update order status
                order.status = OrderStatus.REFUNDED
                db.commit()
                
                logger.info(f"Initiated refund for transaction {transaction_id}")
                return {
                    "success": True,
                    "refund_id": result["refund_id"],
                    "status": result["status"],
                    "amount": result["amount"],
                    "transaction_id": transaction_id
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Error initiating refund: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_transaction_history", args_schema=GetTransactionHistoryInput)
    def get_transaction_history(self, customer_email: str, limit: int = 10) -> Dict[str, Any]:
        """Get transaction history for a customer."""
        try:
            result = self.payment_service.get_transaction_history(
                customer_email=customer_email,
                limit=limit
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "transactions": result["transactions"],
                    "total": result["total"],
                    "customer_email": customer_email
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_payment_status", args_schema=GetPaymentStatusInput)
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get payment status for a transaction."""
        try:
            # Check our database first
            db = next(get_db())
            order = db.query(Order).filter(
                Order.flutterwave_transaction_id == transaction_id
            ).first()
            
            if order:
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "order_id": order.id,
                    "status": order.status.value,
                    "amount": order.amount,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                    "source": "database"
                }
            else:
                # Try to verify with Flutterwave
                result = self.payment_service.verify_transaction(transaction_id)
                if result["success"]:
                    return {
                        "success": True,
                        "transaction_id": result["transaction_id"],
                        "status": result["status"],
                        "amount": result["amount"],
                        "currency": result["currency"],
                        "customer_email": result["customer_email"],
                        "created_at": result["created_at"],
                        "source": "flutterwave"
                    }
                else:
                    return {"success": False, "error": self.TRANSACTION_NOT_FOUND}
                
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("check_order_payment_status", args_schema=dict)
    def check_order_payment_status(self, order_id: int) -> Dict[str, Any]:
        """Check payment status for an order."""
        try:
            db = next(get_db())
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                return {"success": False, "error": self.ORDER_NOT_FOUND}
            
            # If order has Flutterwave transaction ID, verify with Flutterwave
            if order.flutterwave_transaction_id:
                verification_result = self.payment_service.verify_transaction(
                    order.flutterwave_transaction_id
                )
                
                if verification_result["success"]:
                    # Update order status if it has changed
                    if verification_result["status"] == "successful" and order.status != OrderStatus.PAID:
                        order.status = OrderStatus.PAID
                        db.commit()
                    elif verification_result["status"] == "failed" and order.status == OrderStatus.PENDING:
                        order.status = OrderStatus.FAILED
                        db.commit()
            
            return {
                "success": True,
                "order_id": order_id,
                "status": order.status.value,
                "amount": order.amount,
                "payment_link": order.payment_link,
                "payment_link_expires_at": order.payment_link_expires_at.isoformat() if order.payment_link_expires_at else None,
                "flutterwave_transaction_id": order.flutterwave_transaction_id,
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
            
        except Exception as e:
            logger.error(f"Error checking order payment status: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("update_order_payment_info", args_schema=dict)
    def update_order_payment_info(self, order_id: int, payment_link: Optional[str] = None,
                                 flutterwave_payment_id: Optional[str] = None,
                                 flutterwave_transaction_id: Optional[str] = None) -> Dict[str, Any]:
        """Update payment information for an order."""
        try:
            db = next(get_db())
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                return {"success": False, "error": self.ORDER_NOT_FOUND}
            
            # Update payment information
            if payment_link is not None:
                order.payment_link = payment_link
            if flutterwave_payment_id is not None:
                order.flutterwave_payment_id = flutterwave_payment_id
            if flutterwave_transaction_id is not None:
                order.flutterwave_transaction_id = flutterwave_transaction_id
            
            order.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"Updated payment info for order {order_id}")
            return {
                "success": True,
                "message": "Order payment information updated successfully",
                "order_id": order_id
            }
            
        except Exception as e:
            logger.error(f"Error updating order payment info: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_payment_analytics(self) -> Dict[str, Any]:
        """Get payment analytics and statistics."""
        try:
            db = next(get_db())
            
            # Get order statistics
            total_orders = db.query(Order).count()
            pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
            paid_orders = db.query(Order).filter(Order.status == OrderStatus.PAID).count()
            failed_orders = db.query(Order).filter(Order.status == OrderStatus.FAILED).count()
            
            # Get total revenue
            paid_orders_query = db.query(Order).filter(Order.status == OrderStatus.PAID)
            total_revenue = sum(order.amount for order in paid_orders_query.all())
            
            return {
                "success": True,
                "analytics": {
                    "total_orders": total_orders,
                    "pending_orders": pending_orders,
                    "paid_orders": paid_orders,
                    "failed_orders": failed_orders,
                    "total_revenue": total_revenue,
                    "conversion_rate": (paid_orders / total_orders * 100) if total_orders > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting payment analytics: {e}")
            return {"success": False, "error": str(e)}
