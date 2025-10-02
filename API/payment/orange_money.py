# Orange Money Payment API
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

router = APIRouter(prefix="/payment/orange-money", tags=["Orange Money Payment"])
logger = logging.getLogger(__name__)

class PaymentRequest(BaseModel):
    amount: float
    currency: str = "XAF"
    phone_number: str
    description: str
    order_id: str

class PaymentResponse(BaseModel):
    transaction_id: str
    status: str
    payment_url: Optional[str] = None
    amount: float
    currency: str

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(request: PaymentRequest):
    """Initiate Orange Money payment"""
    try:
        logger.info(f"Initiating payment: {request.amount} {request.currency} for {request.phone_number}")
        
        # This will integrate with actual Orange Money API
        response = PaymentResponse(
            transaction_id="txn_123456",
            status="pending",
            payment_url="https://payment.orange.com/pay/123456",
            amount=request.amount,
            currency=request.currency
        )
        
        return response
    except Exception as e:
        logger.error(f"Error initiating payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate payment")

@router.get("/status/{transaction_id}")
async def get_payment_status(transaction_id: str):
    """Get payment status"""
    try:
        logger.info(f"Checking payment status: {transaction_id}")
        
        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "amount": 1000.0,
            "currency": "XAF",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment status")

@router.post("/refund/{transaction_id}")
async def refund_payment(transaction_id: str, amount: Optional[float] = None):
    """Refund payment"""
    try:
        logger.info(f"Processing refund for transaction: {transaction_id}")
        
        return {
            "refund_id": "ref_123456",
            "transaction_id": transaction_id,
            "status": "refunded",
            "amount": amount or 1000.0,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        raise HTTPException(status_code=500, detail="Failed to process refund")
