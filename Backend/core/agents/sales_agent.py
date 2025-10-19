"""
Sales Agent for Agentic AI System

This agent handles the sales process, including lead qualification, objection handling,
and guiding users through the purchase decision process.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SalesAgent(BaseAgent):
    """
    Agent responsible for sales process and lead qualification.
    
    This agent handles the sales conversation flow, addresses objections,
    and guides users through the purchase decision process.
    """
    
    def __init__(self):
        """Initialize the sales agent."""
        super().__init__(
            agent_id="sales",
            name="Sales Agent",
            description="Handles sales process, lead qualification, and purchase guidance"
        )
        
        # Sales stages
        self.sales_stages = {
            'qualification': 'Understanding customer needs and budget',
            'presentation': 'Presenting product benefits and value',
            'objection_handling': 'Addressing customer concerns',
            'closing': 'Guiding to purchase decision',
            'follow_up': 'Post-purchase support and upselling'
        }
        
        # Common objections and responses
        self.objection_responses = {
            'price': "I understand price is important. Let me show you the value and ROI you'll get from this product.",
            'time': "I know you're busy. This product is designed to save you time and increase your efficiency.",
            'uncertainty': "That's a valid concern. Let me share some success stories and guarantees we offer.",
            'competition': "Great question! Let me explain what makes our product unique and better than alternatives."
        }
        
        logger.info("Sales Agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sales-related input and guide the sales conversation.
        
        Args:
            input_data: Input data containing user message and context
            
        Returns:
            Dictionary containing sales response and guidance
        """
        try:
            user_id = input_data.get('user_id')
            message = input_data.get('message', '')
            conversation_context = input_data.get('conversation_context', {})
            products = input_data.get('products', [])
            
            logger.info(f"Sales Agent processing message from {user_id}: {message}")
            
            # Determine sales stage
            sales_stage = self._determine_sales_stage(message, conversation_context)
            
            # Process based on stage
            response = await self._process_sales_stage(sales_stage, message, products, conversation_context)
            
            # Generate sales suggestions
            suggestions = self._get_sales_suggestions(sales_stage, products)
            
            result = {
                'success': True,
                'response': response,
                'sales_stage': sales_stage,
                'suggestions': suggestions,
                'next_steps': self._get_next_steps(sales_stage),
                'agents_used': ['sales']
            }
            
            # Add to memory
            self.add_to_memory({
                'user_id': user_id,
                'message': message,
                'sales_stage': sales_stage,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Sales Agent processed stage '{sales_stage}' for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in Sales Agent: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm here to help you make the best decision. What questions do you have about our products?",
                'suggestions': ['Product Details', 'Pricing Info', 'Get Help', 'Contact Support']
            }
    
    def _determine_sales_stage(self, message: str, context: Dict[str, Any]) -> str:
        """
        Determine the current sales stage based on message and context.
        
        Args:
            message: User message
            context: Conversation context
            
        Returns:
            Sales stage
        """
        message_lower = message.lower()
        
        # Check for objection patterns
        if any(word in message_lower for word in ['expensive', 'costly', 'price', 'budget', 'afford']):
            return 'objection_handling'
        
        # Check for interest patterns
        if any(word in message_lower for word in ['interested', 'like', 'want', 'need', 'buy', 'purchase']):
            return 'presentation'
        
        # Check for decision patterns
        if any(word in message_lower for word in ['decide', 'choose', 'order', 'checkout', 'buy now']):
            return 'closing'
        
        # Check for follow-up patterns
        if any(word in message_lower for word in ['after', 'support', 'help', 'question']):
            return 'follow_up'
        
        # Default based on context
        current_flow = context.get('current_flow', 'greeting')
        if current_flow == 'sales_process':
            return 'qualification'
        
        return 'qualification'
    
    async def _process_sales_stage(self, stage: str, message: str, products: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Process the sales conversation based on the current stage.
        
        Args:
            stage: Current sales stage
            message: User message
            products: Available products
            context: Conversation context
            
        Returns:
            Sales response
        """
        if stage == 'qualification':
            return self._handle_qualification(message, products)
        elif stage == 'presentation':
            return self._handle_presentation(message, products)
        elif stage == 'objection_handling':
            return self._handle_objections(message, products)
        elif stage == 'closing':
            return self._handle_closing(message, products)
        elif stage == 'follow_up':
            return self._handle_follow_up(message, products)
        else:
            return self._handle_qualification(message, products)
    
    def _handle_qualification(self, message: str, products: List[Dict[str, Any]]) -> str:
        """Handle customer qualification stage."""
        if products:
            product_names = [p['name'] for p in products[:2]]
            return f"Great! I can see you're interested in our products. 🎯\n\nI'd love to help you find the perfect solution. To give you the best recommendation, could you tell me:\n\n• What's your main goal with this product?\n• What's your experience level?\n• What's your budget range?\n\nThis will help me suggest the best option from our {len(products)} available products! 💫"
        else:
            return "I'd love to help you find the perfect product! 🎯\n\nTo give you the best recommendation, could you tell me:\n\n• What are you looking to learn or achieve?\n• What's your experience level?\n• What's your budget range?\n\nThis will help me suggest the best solution for you! 💫"
    
    def _handle_presentation(self, message: str, products: List[Dict[str, Any]]) -> str:
        """Handle product presentation stage."""
        if products:
            product = products[0]  # Focus on first product
            return f"Perfect! Let me tell you why **{product['name']}** is perfect for you: 🌟\n\n✨ **Key Benefits:**\n• Comprehensive learning experience\n• Practical, hands-on approach\n• Lifetime access to materials\n• Community support included\n\n💰 **Investment:** ${product['price']}\n\n🎯 **What you'll get:**\n{product.get('description', 'Complete learning experience with practical applications')}\n\nThis is an investment in your future success! Would you like to proceed with the purchase? 🚀"
        else:
            return "I'm excited to present our amazing products to you! 🌟\n\nOur products are designed to:\n• Provide practical, real-world skills\n• Offer comprehensive learning experiences\n• Include lifetime access and support\n• Deliver measurable results\n\nWhat specific area are you most interested in? I can show you the perfect product for your needs! 💫"
    
    def _handle_objections(self, message: str, products: List[Dict[str, Any]]) -> str:
        """Handle customer objections."""
        message_lower = message.lower()
        
        # Identify objection type
        if any(word in message_lower for word in ['expensive', 'costly', 'price', 'budget']):
            objection_type = 'price'
        elif any(word in message_lower for word in ['time', 'busy', 'schedule']):
            objection_type = 'time'
        elif any(word in message_lower for word in ['sure', 'uncertain', 'doubt', 'think']):
            objection_type = 'uncertainty'
        elif any(word in message_lower for word in ['alternative', 'competitor', 'other']):
            objection_type = 'competition'
        else:
            objection_type = 'general'
        
        base_response = self.objection_responses.get(objection_type, "I understand your concern. Let me address that for you.")
        
        if products and objection_type == 'price':
            product = products[0]
            return f"{base_response}\n\n💰 **Value Breakdown:**\n• ${product['price']} one-time investment\n• Lifetime access to materials\n• Community support worth $200+/month\n• Skills that can increase your income\n\n🎯 **ROI:** This product pays for itself with just one successful project!\n\nWould you like to see our flexible payment options? 💳"
        
        return f"{base_response}\n\nI'm here to help you make the best decision. What specific concerns do you have? I'd love to address them! 🤝"
    
    def _handle_closing(self, message: str, products: List[Dict[str, Any]]) -> str:
        """Handle closing stage."""
        if products:
            product = products[0]
            return f"Excellent choice! 🎉 You're about to invest in **{product['name']}** - a decision that will transform your skills! 🚀\n\n✅ **What happens next:**\n• Secure payment through our trusted system\n• Instant access to all materials\n• Welcome to our community\n• Start learning immediately\n\n💰 **Total Investment:** ${product['price']}\n\nReady to get started? I'll guide you through the secure checkout process! 💳✨"
        else:
            return "I'm excited to help you get started! 🎉\n\n✅ **Next Steps:**\n• Choose your preferred product\n• Secure payment process\n• Instant access to materials\n• Join our learning community\n\nWhat product would you like to purchase? I'll guide you through the checkout! 💳✨"
    
    def _handle_follow_up(self, message: str, products: List[Dict[str, Any]]) -> str:
        """Handle follow-up stage."""
        return "Thank you for your interest! 🙏\n\nI'm here to support you throughout your learning journey. Whether you have questions about our products, need technical support, or want to explore additional options, I'm here to help!\n\nWhat can I assist you with today? 🤝"
    
    def _get_sales_suggestions(self, stage: str, products: List[Dict[str, Any]]) -> List[str]:
        """Get suggestion buttons based on sales stage."""
        suggestions = {
            'qualification': ['Tell Me More', 'See Products', 'Pricing Info', 'Get Help'],
            'presentation': ['Buy Now', 'Payment Options', 'More Details', 'Get Help'],
            'objection_handling': ['Address Concerns', 'Payment Plans', 'Guarantees', 'Get Help'],
            'closing': ['Complete Purchase', 'Payment Options', 'Contact Support', 'Get Help'],
            'follow_up': ['Product Support', 'Additional Products', 'Contact Us', 'Get Help']
        }
        
        return suggestions.get(stage, ['Get Help', 'Contact Support'])
    
    def _get_next_steps(self, stage: str) -> List[str]:
        """Get next steps based on sales stage."""
        next_steps = {
            'qualification': ['product_presentation', 'needs_assessment'],
            'presentation': ['objection_handling', 'value_demonstration'],
            'objection_handling': ['closing', 'follow_up'],
            'closing': ['payment_process', 'order_confirmation'],
            'follow_up': ['support_provision', 'upselling']
        }
        
        return next_steps.get(stage, ['general_assistance'])
    
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities.
        
        Returns:
            List of capability strings
        """
        return [
            'lead_qualification',
            'product_presentation',
            'objection_handling',
            'sales_closing',
            'follow_up',
            'value_demonstration',
            'purchase_guidance',
            'customer_support'
        ]
    
    def get_sales_stats(self) -> Dict[str, Any]:
        """
        Get sales agent statistics.
        
        Returns:
            Dictionary containing sales stats
        """
        memory_items = self.get_memory(limit=100)
        
        # Count sales stages
        stage_counts = {}
        for item in memory_items:
            stage = item.get('sales_stage', 'unknown')
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        return {
            'total_sales_interactions': len(memory_items),
            'stage_distribution': stage_counts,
            'last_activity': self.last_activity.isoformat(),
            'memory_size': len(self.memory)
        }
