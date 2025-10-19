"""
Conversation Agent for Agentic AI System

This agent handles general conversation flow, greetings, and basic user interactions.
It serves as the entry point for most user interactions.
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

from .base_agent import BaseAgent
from ..ai.ai_controller import ai_controller

logger = logging.getLogger(__name__)

class ConversationAgent(BaseAgent):
    """
    Agent responsible for handling general conversation flow and greetings.
    
    This agent manages the initial user interaction and determines the appropriate
    conversation direction based on user input.
    """
    
    def __init__(self):
        """Initialize the conversation agent."""
        super().__init__(
            agent_id="conversation",
            name="Conversation Agent",
            description="Handles general conversation flow and user greetings"
        )
        
        # Conversation patterns
        self.greeting_patterns = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
            'start', 'begin', 'help', 'assist'
        ]
        
        self.product_inquiry_patterns = [
            'product', 'course', 'learn', 'education', 'training', 'skill',
            'digital', 'online', 'tutorial', 'guide'
        ]
        
        self.pricing_patterns = [
            'price', 'cost', 'fee', 'payment', 'buy', 'purchase', 'order',
            'expensive', 'cheap', 'affordable'
        ]
        
        logger.info("Conversation Agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process conversation input and determine appropriate response.
        
        Args:
            input_data: Input data containing user message and context
            
        Returns:
            Dictionary containing conversation response
        """
        try:
            user_id = input_data.get('user_id')
            message = input_data.get('message', '')
            conversation_context = input_data.get('conversation_context', {})
            
            logger.info(f"Conversation Agent processing message from {user_id}: {message}")
            
            # Analyze message intent
            intent = self._analyze_intent(message)
            
            # Generate appropriate response
            response = await self._generate_response(message, intent, conversation_context)
            
            # Determine next steps
            next_steps = self._determine_next_steps(intent, conversation_context)
            
            result = {
                'success': True,
                'response': response,
                'intent': intent,
                'next_steps': next_steps,
                'suggestions': self._get_suggestions(intent),
                'agents_used': ['conversation']
            }
            
            # Add to memory
            self.add_to_memory({
                'user_id': user_id,
                'message': message,
                'intent': intent,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Conversation Agent response: {response[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error in Conversation Agent: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Hello! I'm here to help you. How can I assist you today?",
                'suggestions': ['View Products', 'Get Help', 'Contact Support']
            }
    
    def _analyze_intent(self, message: str) -> str:
        """
        Analyze user message to determine intent.
        
        Args:
            message: User message
            
        Returns:
            Detected intent
        """
        message_lower = message.lower()
        
        # Check for greeting
        if any(pattern in message_lower for pattern in self.greeting_patterns):
            return 'greeting'
        
        # Check for product inquiry
        if any(pattern in message_lower for pattern in self.product_inquiry_patterns):
            return 'product_inquiry'
        
        # Check for pricing inquiry
        if any(pattern in message_lower for pattern in self.pricing_patterns):
            return 'pricing_inquiry'
        
        # Check for support request
        if any(word in message_lower for word in ['help', 'support', 'problem', 'issue', 'error']):
            return 'support_request'
        
        # Default to general inquiry
        return 'general_inquiry'
    
    async def _generate_response(self, message: str, intent: str, context: Dict[str, Any]) -> str:
        """
        Generate appropriate response based on intent.
        
        Args:
            message: User message
            intent: Detected intent
            context: Conversation context
            
        Returns:
            Generated response
        """
        try:
            # Use AI controller for response generation
            if hasattr(ai_controller, 'model') and ai_controller.model:
                response, suggestions = ai_controller.generate_response(
                    user_message=message,
                    user_id=context.get('user_id', 'unknown'),
                    chat_history=context.get('history', []),
                    current_stage=intent
                )
                return response
            else:
                # Fallback responses
                return self._get_fallback_response(intent)
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(intent)
    
    def _get_fallback_response(self, intent: str) -> str:
        """
        Get fallback response when AI is not available.
        
        Args:
            intent: Detected intent
            
        Returns:
            Fallback response
        """
        responses = {
            'greeting': "Hello! 👋 Welcome to Isabi! I'm your AI assistant here to help you find amazing digital products. What can I help you with today?",
            'product_inquiry': "Great! 🛍️ I'd love to help you find the perfect digital products. What type of products or skills are you interested in learning about?",
            'pricing_inquiry': "I'd be happy to help you with pricing information! 💰 What specific product or course are you interested in?",
            'support_request': "I'm here to help! 🤝 What kind of support do you need? I can assist with product information, orders, payments, or general questions.",
            'general_inquiry': "Thanks for your message! 😊 I'm here to help you with our digital products and services. What would you like to know more about?"
        }
        
        return responses.get(intent, responses['general_inquiry'])
    
    def _determine_next_steps(self, intent: str, context: Dict[str, Any]) -> List[str]:
        """
        Determine next steps based on intent and context.
        
        Args:
            intent: Detected intent
            context: Conversation context
            
        Returns:
            List of next steps
        """
        next_steps = []
        
        if intent == 'greeting':
            next_steps = ['product_inquiry', 'pricing_inquiry']
        elif intent == 'product_inquiry':
            next_steps = ['product_search', 'product_details']
        elif intent == 'pricing_inquiry':
            next_steps = ['pricing_info', 'payment_options']
        elif intent == 'support_request':
            next_steps = ['support_escalation', 'faq_search']
        else:
            next_steps = ['general_assistance']
        
        return next_steps
    
    def _get_suggestions(self, intent: str) -> List[str]:
        """
        Get suggestion buttons based on intent.
        
        Args:
            intent: Detected intent
            
        Returns:
            List of suggestions
        """
        suggestions = {
            'greeting': ['View Products', 'Course Info', 'Pricing', 'Get Help'],
            'product_inquiry': ['AI Courses', 'Digital Items', 'Show All', 'Get Help'],
            'pricing_inquiry': ['View Pricing', 'Payment Options', 'Order Now', 'Get Help'],
            'support_request': ['Product Help', 'Payment Help', 'Contact Support', 'FAQ'],
            'general_inquiry': ['View Products', 'Get Help', 'Contact Support']
        }
        
        return suggestions.get(intent, ['Get Help', 'Contact Support'])
    
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities.
        
        Returns:
            List of capability strings
        """
        return [
            'conversation_flow',
            'intent_analysis',
            'greeting_handling',
            'response_generation',
            'context_management',
            'suggestion_provision'
        ]
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Get conversation statistics.
        
        Returns:
            Dictionary containing conversation stats
        """
        memory_items = self.get_memory(limit=100)
        
        # Count intents
        intent_counts = {}
        for item in memory_items:
            intent = item.get('intent', 'unknown')
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return {
            'total_conversations': len(memory_items),
            'intent_distribution': intent_counts,
            'last_activity': self.last_activity.isoformat(),
            'memory_size': len(self.memory)
        }
