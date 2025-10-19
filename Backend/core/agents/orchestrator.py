"""
Agent Orchestrator for Agentic AI System

This module provides the orchestrator that coordinates multiple agents to handle
complex conversations and tasks in the WhatsApp sales bot.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio

from .base_agent import BaseAgent
from .sales_agent import SalesAgent
from .product_agent import ProductAgent
from .payment_agent import PaymentAgent
from .conversation_agent import ConversationAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Orchestrator that coordinates multiple agents to handle complex tasks.
    
    This class manages the flow between different agents and ensures proper
    coordination for multi-step processes like sales conversations.
    """
    
    def __init__(self):
        """Initialize the agent orchestrator."""
        self.agents: Dict[str, BaseAgent] = {}
        self.conversation_flows: Dict[str, List[str]] = {}
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
        # Initialize agents
        self._initialize_agents()
        
        logger.info("Agent Orchestrator initialized with all agents")
    
    def _initialize_agents(self):
        """Initialize all available agents."""
        # Create agent instances
        self.agents['conversation'] = ConversationAgent()
        self.agents['sales'] = SalesAgent()
        self.agents['product'] = ProductAgent()
        self.agents['payment'] = PaymentAgent()
        
        # Define conversation flows
        self.conversation_flows = {
            'greeting': ['conversation'],
            'product_inquiry': ['conversation', 'product'],
            'sales_process': ['conversation', 'product', 'sales'],
            'payment_process': ['conversation', 'sales', 'payment'],
            'support': ['conversation']
        }
        
        logger.info(f"Initialized {len(self.agents)} agents")
        logger.info(f"Defined {len(self.conversation_flows)} conversation flows")
    
    async def process_message(self, user_id: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user message through the appropriate agent flow.
        
        Args:
            user_id: User identifier
            message: User message
            context: Additional context
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Get or create conversation context
            if user_id not in self.active_conversations:
                self.active_conversations[user_id] = {
                    'current_flow': 'greeting',
                    'step': 0,
                    'context': context or {},
                    'history': [],
                    'started_at': datetime.now()
                }
            
            conversation = self.active_conversations[user_id]
            
            # Determine the appropriate flow
            flow = self._determine_conversation_flow(message, conversation)
            conversation['current_flow'] = flow
            
            # Process through the flow
            result = await self._process_flow(user_id, message, flow, conversation)
            
            # Update conversation history
            conversation['history'].append({
                'timestamp': datetime.now().isoformat(),
                'user_message': message,
                'flow': flow,
                'response': result
            })
            
            # Keep only last 20 interactions
            if len(conversation['history']) > 20:
                conversation['history'] = conversation['history'][-20:]
            
            logger.info(f"Processed message for user {user_id} through flow '{flow}'")
            return result
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm sorry, I encountered an error. Please try again.",
                'suggestions': ['Get Help', 'Contact Support']
            }
    
    def _determine_conversation_flow(self, message: str, conversation: Dict[str, Any]) -> str:
        """
        Determine the appropriate conversation flow based on message content.
        
        Args:
            message: User message
            conversation: Current conversation context
            
        Returns:
            Flow name
        """
        message_lower = message.lower()
        current_flow = conversation.get('current_flow', 'greeting')
        
        # Check for flow-specific triggers
        if any(word in message_lower for word in ['product', 'course', 'learn', 'buy', 'purchase']):
            return 'product_inquiry'
        elif any(word in message_lower for word in ['price', 'cost', 'payment', 'pay']):
            return 'sales_process'
        elif any(word in message_lower for word in ['order', 'checkout', 'buy now']):
            return 'payment_process'
        elif any(word in message_lower for word in ['help', 'support', 'problem', 'issue']):
            return 'support'
        elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            return 'greeting'
        
        # Default to current flow or greeting
        return current_flow if current_flow != 'greeting' else 'greeting'
    
    async def _process_flow(self, user_id: str, message: str, flow: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process message through the specified flow.
        
        Args:
            user_id: User identifier
            message: User message
            flow: Flow name
            conversation: Conversation context
            
        Returns:
            Processing result
        """
        try:
            flow_agents = self.conversation_flows.get(flow, ['conversation'])
            
            # Prepare input data
            input_data = {
                'user_id': user_id,
                'message': message,
                'flow': flow,
                'conversation_context': conversation,
                'timestamp': datetime.now().isoformat()
            }
            
            # Process through each agent in the flow
            current_result = input_data
            
            for agent_name in flow_agents:
                if agent_name in self.agents:
                    agent = self.agents[agent_name]
                    
                    # Update agent context
                    agent.update_context(conversation.get('context', {}))
                    
                    # Process with agent
                    agent_result = await agent.process(current_result)
                    
                    # Merge results
                    current_result.update(agent_result)
                    
                    # Add to agent memory
                    agent.add_to_memory({
                        'user_id': user_id,
                        'message': message,
                        'result': agent_result,
                        'flow': flow
                    })
                    
                    logger.debug(f"Processed with {agent_name}: {agent_result.get('success', False)}")
            
            # Format final response
            return self._format_response(current_result)
            
        except Exception as e:
            logger.error(f"Error processing flow {flow}: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm sorry, I encountered an error processing your request.",
                'suggestions': ['Try Again', 'Get Help', 'Contact Support']
            }
    
    def _format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the final response from agent processing.
        
        Args:
            result: Agent processing result
            
        Returns:
            Formatted response
        """
        return {
            'success': result.get('success', True),
            'response': result.get('response', 'How can I help you today?'),
            'suggestions': result.get('suggestions', ['Get Help', 'Contact Support']),
            'products': result.get('products', []),
            'payment_link': result.get('payment_link'),
            'metadata': {
                'flow': result.get('flow'),
                'agents_used': result.get('agents_used', []),
                'timestamp': result.get('timestamp')
            }
        }
    
    def get_agent_status(self, agent_id: str = None) -> Dict[str, Any]:
        """
        Get status of specific agent or all agents.
        
        Args:
            agent_id: Specific agent ID, or None for all agents
            
        Returns:
            Agent status information
        """
        if agent_id:
            if agent_id in self.agents:
                return self.agents[agent_id].get_status()
            else:
                return {'error': f'Agent {agent_id} not found'}
        
        return {
            agent_id: agent.get_status() 
            for agent_id, agent in self.agents.items()
        }
    
    def get_conversation_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get status of user conversation.
        
        Args:
            user_id: User identifier
            
        Returns:
            Conversation status
        """
        if user_id in self.active_conversations:
            conversation = self.active_conversations[user_id]
            return {
                'user_id': user_id,
                'current_flow': conversation['current_flow'],
                'step': conversation['step'],
                'history_count': len(conversation['history']),
                'started_at': conversation['started_at'].isoformat(),
                'context_keys': list(conversation['context'].keys())
            }
        else:
            return {'error': f'No active conversation for user {user_id}'}
    
    def reset_conversation(self, user_id: str):
        """
        Reset conversation for a user.
        
        Args:
            user_id: User identifier
        """
        if user_id in self.active_conversations:
            del self.active_conversations[user_id]
            logger.info(f"Reset conversation for user {user_id}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.
        
        Returns:
            System status information
        """
        return {
            'total_agents': len(self.agents),
            'active_conversations': len(self.active_conversations),
            'available_flows': list(self.conversation_flows.keys()),
            'agent_status': {
                agent_id: agent.get_status() 
                for agent_id, agent in self.agents.items()
            }
        }

# Global instance
agent_orchestrator = AgentOrchestrator()
