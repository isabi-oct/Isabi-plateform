"""
Flutterwave Payment API Endpoints

This module provides REST API endpoints for Flutterwave payment operations:
- Payment initialization
- Transaction verification
- Webhook handling
- Refund processing
- Transaction history

Author: AI Assistant
Created: 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from Backend.models.database.models import Order, OrderStatus, User
from Backend.services.payment_service import payment_service
from Backend.models.database.database import get_db
from Backend.config.settings import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models for request/response validation
class PaymentRequest(BaseModel):
    """Model for payment initialization request."""
    amount: float
    product_name: str
    order_id: int
    customer_email: EmailStr
    customer_name: str
    customer_phone: str

class PaymentResponse(BaseModel):
    """Model for payment initialization response."""
    success: bool
    payment_link: Optional[str] = None
    transaction_reference: Optional[str] = None
    flutterwave_reference: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None

class TransactionVerificationRequest(BaseModel):
    """Model for transaction verification request."""
    transaction_id: str

class TransactionVerificationResponse(BaseModel):
    """Model for transaction verification response."""
    success: bool
    transaction_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    customer_email: Optional[str] = None
    payment_type: Optional[str] = None
    created_at: Optional[datetime] = None
    tx_ref: Optional[str] = None
    error: Optional[str] = None

class RefundRequest(BaseModel):
    """Model for refund request."""
    transaction_id: str
    amount: Optional[float] = None
    reason: str = "Customer request"

class RefundResponse(BaseModel):
    """Model for refund response."""
    success: bool
    refund_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    error: Optional[str] = None

class TransactionHistoryRequest(BaseModel):
    """Model for transaction history request."""
    customer_email: EmailStr
    limit: int = 10

class TransactionHistoryResponse(BaseModel):
    """Model for transaction history response."""
    success: bool
    transactions: Optional[list] = None
    total: Optional[int] = None
    error: Optional[str] = None

@router.post("/initialize", response_model=PaymentResponse)
async def initialize_payment(
    payment_request: PaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Initialize a Flutterwave payment for an order.
    
    This endpoint creates a payment link that customers can use to complete their payment.
    The payment link expires after a configured time period.
    """
    try:
        # Validate order exists
        order = db.query(Order).filter(Order.id == payment_request.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if order is in pending status
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=400, detail="Order is not in pending status")
        
        # Create payment link
        result = payment_service.create_payment_link(
            amount=payment_request.amount,
            product_name=payment_request.product_name,
            order_id=payment_request.order_id,
            customer_email=payment_request.customer_email,
            customer_name=payment_request.customer_name,
            customer_phone=payment_request.customer_phone
        )
        
        if result["success"]:
            # Update order with payment details
            order.payment_link = result["payment_link"]
            order.payment_link_expires_at = result["expires_at"]
            order.flutterwave_payment_id = result["flutterwave_reference"]
            order.flutterwave_transaction_id = result["transaction_reference"]
            db.commit()
            
            return PaymentResponse(
                success=True,
                payment_link=result["payment_link"],
                transaction_reference=result["transaction_reference"],
                flutterwave_reference=result["flutterwave_reference"],
                expires_at=result["expires_at"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/verify", response_model=TransactionVerificationResponse)
async def verify_transaction(
    verification_request: TransactionVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a Flutterwave transaction.
    
    This endpoint verifies the status of a transaction using the Flutterwave transaction ID.
    """
    try:
        result = payment_service.verify_transaction(verification_request.transaction_id)
        
        if result["success"]:
            # Update order status if payment is successful
            if result["status"] == "successful":
                order = db.query(Order).filter(
                    Order.flutterwave_transaction_id == result["tx_ref"]
                ).first()
                
                if order:
                    order.status = OrderStatus.PAID
                    order.flutterwave_transaction_id = result["transaction_id"]
                    db.commit()
            
            return TransactionVerificationResponse(
                success=True,
                transaction_id=result["transaction_id"],
                status=result["status"],
                amount=result["amount"],
                currency=result["currency"],
                customer_email=result["customer_email"],
                payment_type=result["payment_type"],
                created_at=result["created_at"],
                tx_ref=result["tx_ref"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Flutterwave webhook notifications.
    
    This endpoint processes webhook notifications from Flutterwave for payment events
    such as payment completion, failure, or refunds.
    """
    try:
        # Get webhook signature
        signature = request.headers.get("verif-hash")
        if not signature:
            logger.warning("No webhook signature provided")
            raise HTTPException(status_code=400, detail="Missing webhook signature")
        
        # Get request body
        payload = await request.json()
        
        # Process webhook
        result = payment_service.process_webhook(payload, signature)
        
        if result["success"]:
            # Handle webhook processing in background
            background_tasks.add_task(
                _process_webhook_background,
                payload,
                db
            )
            
            return JSONResponse(
                status_code=200,
                content={"status": "success", "message": "Webhook processed successfully"}
            )
        else:
            logger.error(f"Webhook processing failed: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _process_webhook_background(payload: Dict[str, Any], db: Session):
    """Background task to process webhook data."""
    try:
        event_type = payload.get("event")
        data = payload.get("data", {})
        
        if event_type == "charge.completed":
            tx_ref = data.get("tx_ref")
            transaction_id = data.get("id")
            status = data.get("status")
            
            if status == "successful":
                # Update order status
                order = db.query(Order).filter(
                    Order.flutterwave_transaction_id == tx_ref
                ).first()
                
                if order:
                    order.status = OrderStatus.PAID
                    order.flutterwave_transaction_id = transaction_id
                    db.commit()
                    logger.info(f"Order {order.id} marked as paid via webhook")
        
        elif event_type == "charge.failed":
            tx_ref = data.get("tx_ref")
            transaction_id = data.get("id")
            
            # Update order status to failed
            order = db.query(Order).filter(
                Order.flutterwave_transaction_id == tx_ref
            ).first()
            
            if order:
                order.status = OrderStatus.FAILED
                db.commit()
                logger.info(f"Order {order.id} marked as failed via webhook")
                
    except Exception as e:
        logger.error(f"Error in background webhook processing: {str(e)}")

@router.post("/refund", response_model=RefundResponse)
async def initiate_refund(
    refund_request: RefundRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate a refund for a Flutterwave transaction.
    
    This endpoint initiates a refund for a completed transaction.
    """
    try:
        # Verify transaction exists
        order = db.query(Order).filter(
            Order.flutterwave_transaction_id == refund_request.transaction_id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Check if order is paid
        if order.status != OrderStatus.PAID:
            raise HTTPException(status_code=400, detail="Cannot refund unpaid order")
        
        # Initiate refund
        result = payment_service.initiate_refund(
            transaction_id=refund_request.transaction_id,
            amount=refund_request.amount,
            reason=refund_request.reason
        )
        
        if result["success"]:
            # Update order status
            order.status = OrderStatus.REFUNDED
            db.commit()
            
            return RefundResponse(
                success=True,
                refund_id=result["refund_id"],
                status=result["status"],
                amount=result["amount"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating refund: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/history", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    history_request: TransactionHistoryRequest,
    db: Session = Depends(get_db)
):
    """
    Get transaction history for a customer.
    
    This endpoint retrieves the transaction history for a specific customer.
    """
    try:
        result = payment_service.get_transaction_history(
            customer_email=history_request.customer_email,
            limit=history_request.limit
        )
        
        if result["success"]:
            return TransactionHistoryResponse(
                success=True,
                transactions=result["transactions"],
                total=result["total"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transaction history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/status/{transaction_id}")
async def get_payment_status(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the current status of a payment transaction.
    
    This endpoint returns the current status of a payment transaction.
    """
    try:
        # Get order from database
        order = db.query(Order).filter(
            Order.flutterwave_transaction_id == transaction_id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "order_id": order.id,
            "status": order.status.value,
            "amount": order.amount,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for Flutterwave payment service.
    
    This endpoint verifies that the payment service is operational.
    """
    try:
        # Test Flutterwave API connectivity
        test_response = payment_service.get_transaction_history("test@example.com", 1)
        
        return {
            "status": "healthy",
            "service": "flutterwave-payment",
            "timestamp": datetime.utcnow().isoformat(),
            "api_status": "connected" if test_response["success"] else "disconnected"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "flutterwave-payment",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
