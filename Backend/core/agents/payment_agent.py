"""
Payment Agent for Agentic AI System

This agent handles payment processing, order management, and transaction-related tasks.
It integrates with Flutterwave payment system and manages the complete payment flow.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from .base_agent import BaseAgent
from Backend.models.database.database import get_db
from Backend.models.database.models import Order, OrderStatus, User, Product
from ...services.payment_service import payment_service

logger = logging.getLogger(__name__)

class PaymentAgent(BaseAgent):
    """
    Agent responsible for payment processing and order management.
    
    This agent handles payment initialization, transaction verification,
    order status updates, and payment-related customer support.
    """
    
    def __init__(self):
        """Initialize the payment agent."""
        super().__init__(
            agent_id="payment",
            name="Payment Agent",
            description="Handles payment processing, order management, and transaction support"
        )
        
        # Payment statuses
        self.payment_statuses = {
            'pending': 'Payment is being processed',
            'completed': 'Payment completed successfully',
            'failed': 'Payment failed',
            'cancelled': 'Payment was cancelled',
            'refunded': 'Payment was refunded'
        }
        
        # Payment methods
        self.payment_methods = [
            'card', 'bank_transfer', 'mobile_money', 'paypal', 'apple_pay', 'google_pay'
        ]
        
        logger.info("Payment Agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process payment-related input and handle payment operations.
        
        Args:
            input_data: Input data containing user message and context
            
        Returns:
            Dictionary containing payment response and actions
        """
        try:
            user_id = input_data.get('user_id')
            message = input_data.get('message', '')
            conversation_context = input_data.get('conversation_context', {})
            products = input_data.get('products', [])
            
            logger.info(f"Payment Agent processing message from {user_id}: {message}")
            
            # Determine payment intent
            payment_intent = self._analyze_payment_intent(message)
            
            # Process payment request
            result = await self._process_payment_request(payment_intent, message, products, conversation_context, user_id)
            
            # Add to memory
            self.add_to_memory({
                'user_id': user_id,
                'message': message,
                'payment_intent': payment_intent,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Payment Agent processed intent '{payment_intent}' for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in Payment Agent: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm having trouble with the payment system right now. Please try again or contact support.",
                'suggestions': ['Try Again', 'Contact Support', 'Get Help']
            }
    
    def _analyze_payment_intent(self, message: str) -> str:
        """
        Analyze message to determine payment intent.
        
        Args:
            message: User message
            
        Returns:
            Payment intent
        """
        message_lower = message.lower()
        
        # Check for payment initiation
        if any(word in message_lower for word in ['pay', 'payment', 'buy', 'purchase', 'order', 'checkout']):
            return 'initiate_payment'
        
        # Check for payment status inquiry
        if any(word in message_lower for word in ['status', 'paid', 'completed', 'successful']):
            return 'check_payment_status'
        
        # Check for payment method inquiry
        if any(word in message_lower for word in ['method', 'card', 'bank', 'mobile', 'paypal']):
            return 'payment_methods'
        
        # Check for refund request
        if any(word in message_lower for word in ['refund', 'return', 'cancel', 'money back']):
            return 'refund_request'
        
        # Check for payment issues
        if any(word in message_lower for word in ['problem', 'issue', 'error', 'failed', 'not working']):
            return 'payment_support'
        
        # Default to payment initiation
        return 'initiate_payment'
    
    async def _process_payment_request(self, intent: str, message: str, products: List[Dict[str, Any]], 
                                     context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Process payment request based on intent.
        
        Args:
            intent: Payment intent
            message: User message
            products: Available products
            context: Conversation context
            user_id: User identifier
            
        Returns:
            Payment processing result
        """
        if intent == 'initiate_payment':
            return await self._initiate_payment(products, user_id, context)
        elif intent == 'check_payment_status':
            return await self._check_payment_status(message, user_id)
        elif intent == 'payment_methods':
            return await self._get_payment_methods()
        elif intent == 'refund_request':
            return await self._handle_refund_request(message, user_id)
        elif intent == 'payment_support':
            return await self._handle_payment_support(message, user_id)
        else:
            return await self._initiate_payment(products, user_id, context)
    
    async def _initiate_payment(self, products: List[Dict[str, Any]], user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate payment process for selected products."""
        try:
            if not products:
                return {
                    'success': False,
                    'response': "I don't see any products selected for purchase. Please choose a product first! 🛍️",
                    'suggestions': ['View Products', 'Get Help', 'Contact Support']
                }
            
            # Get user information
            user_info = await self._get_user_info(user_id)
            if not user_info:
                return {
                    'success': False,
                    'response': "I need some information to process your payment. Could you provide your email address? 📧",
                    'suggestions': ['Provide Email', 'Get Help', 'Contact Support']
                }
            
            # Select first product for payment
            product = products[0]
            
            # Create order
            order = await self._create_order(user_id, product, user_info)
            if not order:
                return {
                    'success': False,
                    'response': "I'm having trouble creating your order. Please try again or contact support. 🔧",
                    'suggestions': ['Try Again', 'Contact Support', 'Get Help']
                }
            
            # Initialize payment
            payment_result = payment_service.create_payment_link(
                amount=product['price'],
                product_name=product['name'],
                order_id=order['id'],
                customer_email=user_info['email'],
                customer_name=user_info.get('name', 'Customer'),
                customer_phone=user_info.get('phone', '')
            )
            
            if payment_result['success']:
                return {
                    'success': True,
                    'response': f"Perfect! 🎉 I've prepared your payment for **{product['name']}** (${product['price']})\n\n💳 **Payment Link:** {payment_result['payment_link']}\n\n✅ **What's included:**\n• Secure payment processing\n• Instant access after payment\n• Email confirmation\n• Customer support\n\nClick the link above to complete your secure payment! 🚀",
                    'payment_link': payment_result['payment_link'],
                    'order_id': order['id'],
                    'suggestions': ['Complete Payment', 'Payment Help', 'Contact Support']
                }
            else:
                return {
                    'success': False,
                    'response': f"I encountered an issue creating your payment link: {payment_result.get('error', 'Unknown error')}\n\nPlease try again or contact support for assistance. 🔧",
                    'suggestions': ['Try Again', 'Contact Support', 'Get Help']
                }
                
        except Exception as e:
            logger.error(f"Error initiating payment: {e}")
            return {
                'success': False,
                'response': "I'm having trouble processing your payment request. Please try again or contact support. 🔧",
                'suggestions': ['Try Again', 'Contact Support', 'Get Help']
            }
    
    async def _check_payment_status(self, message: str, user_id: str) -> Dict[str, Any]:
        """Check payment status for user."""
        try:
            # Get user's recent orders
            db = next(get_db())
            user = db.query(User).filter(User.phone_number == user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'response': "I couldn't find your account. Please make sure you're using the same phone number you used for the order. 📱",
                    'suggestions': ['Provide Phone Number', 'Contact Support', 'Get Help']
                }
            
            # Get recent orders
            orders = db.query(Order).filter(
                Order.user_id == user.id
            ).order_by(Order.created_at.desc()).limit(5).all()
            
            if not orders:
                return {
                    'success': False,
                    'response': "I don't see any orders in your account. Would you like to make a purchase? 🛍️",
                    'suggestions': ['View Products', 'Make Purchase', 'Get Help']
                }
            
            # Format order status
            order_info = []
            for order in orders:
                status_emoji = {
                    OrderStatus.PENDING: '⏳',
                    OrderStatus.PAID: '✅',
                    OrderStatus.EXPIRED: '❌',
                    OrderStatus.CANCELLED: '🚫'
                }.get(order.status, '❓')
                
                order_info.append(f"{status_emoji} Order #{order.id}: {order.status.value} - ${order.amount}")
            
            return {
                'success': True,
                'response': f"Here's your recent order status: 📊\n\n" + "\n".join(order_info) + "\n\nNeed help with any of these orders? I'm here to assist! 🤝",
                'orders': [{'id': o.id, 'status': o.status.value, 'amount': o.amount} for o in orders],
                'suggestions': ['Order Help', 'Payment Help', 'Contact Support']
            }
            
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            return {
                'success': False,
                'response': "I'm having trouble checking your payment status. Please contact support for assistance. 🔧",
                'suggestions': ['Contact Support', 'Get Help']
            }
        finally:
            if 'db' in locals():
                db.close()
    
    async def _get_payment_methods(self) -> Dict[str, Any]:
        """Get available payment methods."""
        return {
            'success': True,
            'response': "We accept multiple secure payment methods: 💳\n\n✅ **Credit/Debit Cards** (Visa, Mastercard, American Express)\n✅ **Bank Transfer**\n✅ **Mobile Money**\n✅ **PayPal**\n✅ **Apple Pay**\n✅ **Google Pay**\n\nAll payments are processed securely through Flutterwave. Your payment information is encrypted and protected! 🔒",
            'payment_methods': self.payment_methods,
            'suggestions': ['Make Payment', 'Payment Help', 'Contact Support']
        }
    
    async def _handle_refund_request(self, message: str, user_id: str) -> Dict[str, Any]:
        """Handle refund requests."""
        return {
            'success': True,
            'response': "I understand you'd like to request a refund. 💰\n\nTo process your refund request, I'll need:\n• Your order number\n• Reason for refund\n• Preferred refund method\n\nPlease provide your order number and I'll help you with the refund process! 📋",
            'suggestions': ['Provide Order Number', 'Refund Policy', 'Contact Support']
        }
    
    async def _handle_payment_support(self, message: str, user_id: str) -> Dict[str, Any]:
        """Handle payment support requests."""
        return {
            'success': True,
            'response': "I'm here to help with any payment issues! 🔧\n\nCommon solutions:\n• Clear browser cache and try again\n• Check your payment method details\n• Ensure sufficient funds\n• Try a different payment method\n\nIf the issue persists, please provide:\n• Error message you're seeing\n• Payment method used\n• Order number (if available)\n\nI'll help you resolve this quickly! 🤝",
            'suggestions': ['Try Again', 'Different Payment Method', 'Contact Support']
        }
    
    async def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information for payment processing."""
        try:
            db = next(get_db())
            user = db.query(User).filter(User.phone_number == user_id).first()
            
            if user:
                return {
                    'email': f"user_{user_id}@isabi.com",  # Default email
                    'name': user.name or 'Customer',
                    'phone': user.phone_number
                }
            else:
                # Create new user
                new_user = User(
                    phone_number=user_id,
                    name='Customer',
                    status='active'
                )
                db.add(new_user)
                db.commit()
                
                return {
                    'email': f"user_{user_id}@isabi.com",
                    'name': 'Customer',
                    'phone': user_id
                }
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
        finally:
            if 'db' in locals():
                db.close()
    
    async def _create_order(self, user_id: str, product: Dict[str, Any], user_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create order for payment processing."""
        try:
            db = next(get_db())
            
            # Get user
            user = db.query(User).filter(User.phone_number == user_id).first()
            if not user:
                return None
            
            # Get product
            product_obj = db.query(Product).filter(Product.id == product['id']).first()
            if not product_obj:
                return None
            
            # Create order
            order = Order(
                user_id=user.id,
                product_id=product_obj.id,
                amount=product['price'],
                status=OrderStatus.PENDING
            )
            
            db.add(order)
            db.commit()
            db.refresh(order)
            
            return {
                'id': order.id,
                'user_id': user.id,
                'product_id': product_obj.id,
                'amount': order.amount,
                'status': order.status.value
            }
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
        finally:
            if 'db' in locals():
                db.close()
    
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities.
        
        Returns:
            List of capability strings
        """
        return [
            'payment_initialization',
            'order_creation',
            'payment_status_check',
            'refund_processing',
            'payment_support',
            'transaction_verification',
            'order_management',
            'customer_payment_assistance'
        ]
    
    def get_payment_stats(self) -> Dict[str, Any]:
        """
        Get payment agent statistics.
        
        Returns:
            Dictionary containing payment stats
        """
        memory_items = self.get_memory(limit=100)
        
        # Count payment intents
        intent_counts = {}
        successful_payments = 0
        
        for item in memory_items:
            intent = item.get('payment_intent', 'unknown')
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            if item.get('result', {}).get('success', False):
                successful_payments += 1
        
        return {
            'total_payment_interactions': len(memory_items),
            'successful_payments': successful_payments,
            'intent_distribution': intent_counts,
            'success_rate': successful_payments / len(memory_items) if memory_items else 0,
            'last_activity': self.last_activity.isoformat()
        }
