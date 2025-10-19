"""
Core Agentic AI System for WhatsApp Product Sales

This module implements the main agentic AI system using LangChain and Vertex AI (Gemini 1.5)
for autonomous reasoning, database access, and tool execution.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import BaseTool
from langchain_core.memory import BaseMemory
from langchain.memory import ConversationBufferWindowMemory

from Backend.config.settings import settings
from Backend.models.database.database import get_db
from Backend.models.database.models import User, Product, Order, ChatSession

logger = logging.getLogger(__name__)

@dataclass
class AgentContext:
    """Context information for agent execution"""
    user_id: str
    message: str
    conversation_history: List[Dict[str, Any]]
    current_session: Optional[ChatSession] = None
    user_profile: Optional[User] = None
    platform: str = "whatsapp"
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class CoreAgent:
    """
    Core Agentic AI system that orchestrates reasoning, tool usage, and responses.
    
    This agent can:
    - Reason autonomously about customer messages
    - Access and modify databases through ORM calls
    - Execute external tools/actions (payments, vector search, etc.)
    - Manage conversation context and memory
    """
    
    def __init__(self):
        """Initialize the core agent with LLM and tools."""
        self.llm = self._initialize_llm()
        self.tools = self._initialize_tools()
        self.memory = self._initialize_memory()
        self.agent_executor = self._create_agent_executor()
        
        logger.info("Core Agentic AI system initialized successfully")
    
    def _initialize_llm(self) -> ChatVertexAI:
        """Initialize the Vertex AI (Gemini 1.5) language model."""
        GEMINI_MODEL = "gemini-1.5-pro"
        
        try:
            # Initialize Vertex AI with Gemini 1.5
            llm = ChatVertexAI(
                model_name=GEMINI_MODEL,
                project=settings.gcp_project_id,
                location=settings.gcp_location,
                temperature=0.1,
                max_output_tokens=2048,
                top_p=0.8,
                top_k=40
            )
            logger.info("Vertex AI (Gemini 1.5) initialized successfully")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            # Fallback to Google Generative AI
            from google.generativeai import GenerativeModel
            model = GenerativeModel(GEMINI_MODEL)
            return model
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize all available tools for the agent."""
        from .tools.db_tools import DatabaseTools
        from .tools.payment_tools import PaymentTools
        from .tools.vector_search_tools import VectorSearchTools
        from .tools.product_tools import ProductTools
        
        tools = []
        
        # Database tools
        db_tools = DatabaseTools()
        tools.extend(db_tools.get_tools())
        
        # Payment tools
        payment_tools = PaymentTools()
        tools.extend(payment_tools.get_tools())
        
        # Vector search tools
        vector_tools = VectorSearchTools()
        tools.extend(vector_tools.get_tools())
        
        # Product tools
        product_tools = ProductTools()
        tools.extend(product_tools.get_tools())
        
        logger.info(f"Initialized {len(tools)} tools for agent")
        return tools
    
    def _initialize_memory(self) -> BaseMemory:
        """Initialize conversation memory."""
        return ConversationBufferWindowMemory(
            k=10,  # Keep last 10 exchanges
            memory_key="chat_history",
            return_messages=True
        )
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create the agent executor with tools and memory."""
        # Define the system prompt
        system_prompt = self._get_system_prompt()
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        # Create the agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the executor
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        return executor
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are iSabi, an intelligent AI sales assistant for digital products. You help customers find and purchase digital products, especially AI-trainable products that include personalized tutoring.

CORE CAPABILITIES:
- Product discovery and recommendations
- Payment processing via Flutterwave
- AI tutoring and Q&A for trainable products
- Vector search for product knowledge
- Order management and tracking
- Customer support

CONVERSATION FLOW:
1. Greet customers warmly and understand their needs
2. Recommend appropriate products (regular or AI-trainable)
3. For AI-trainable products: offer tutoring and Q&A services
4. Process payments securely
5. Provide ongoing support and follow-up

PRODUCT TYPES:
- Regular products: Standard digital products with instant access
- AI-trainable products: Include personalized AI tutoring, Q&A sessions, and ongoing support

TOOLS AVAILABLE:
- Database access for users, products, orders
- Payment processing and verification
- Vector search for product knowledge
- AI tutoring session management
- Order tracking and status updates

RESPONSE GUIDELINES:
- Be friendly, professional, and helpful
- Use emojis appropriately
- Provide clear product information and pricing
- Offer personalized recommendations
- Handle payments securely and transparently
- For AI products, emphasize the tutoring benefits
- Always ask clarifying questions when needed

Remember: You can reason about customer needs, access databases, execute payments, and provide ongoing AI tutoring support. Use your tools effectively to provide the best customer experience."""

    async def process_message(self, context: AgentContext) -> Dict[str, Any]:
        """
        Process a customer message through the agentic AI system.
        
        Args:
            context: AgentContext containing user message and context
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Prepare input for the agent
            agent_input = {
                "input": context.message,
                "chat_history": self._format_conversation_history(context.conversation_history)
            }
            
            # Execute the agent
            result = await self.agent_executor.ainvoke(agent_input)
            
            # Extract response components
            response_text = result.get("output", "I'm here to help! What can I assist you with?")
            
            # Parse any tool calls or actions from the response
            actions = self._extract_actions(result)
            
            # Format the final response
            formatted_response = {
                "success": True,
                "response": response_text,
                "actions": actions,
                "metadata": {
                    "agent_type": "core_agentic_ai",
                    "timestamp": context.timestamp.isoformat(),
                    "user_id": context.user_id,
                    "tools_used": result.get("intermediate_steps", [])
                }
            }
            
            # Update conversation memory
            self._update_memory(context, formatted_response)
            
            logger.info(f"Processed message for user {context.user_id} with agentic AI")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing message with agentic AI: {e}")
            return {
                "success": False,
                "response": "I apologize, but I encountered an error. Please try again or contact support.",
                "error": str(e),
                "metadata": {
                    "agent_type": "core_agentic_ai",
                    "timestamp": context.timestamp.isoformat(),
                    "user_id": context.user_id
                }
            }
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> List[Union[HumanMessage, AIMessage]]:
        """Format conversation history for the agent."""
        messages = []
        for exchange in history[-10:]:  # Keep last 10 exchanges
            if "user_message" in exchange:
                messages.append(HumanMessage(content=exchange["user_message"]))
            if "bot_response" in exchange:
                messages.append(AIMessage(content=exchange["bot_response"]))
        return messages
    
    def _extract_actions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract actions from agent execution result."""
        actions = []
        
        # Check for tool calls in intermediate steps
        intermediate_steps = result.get("intermediate_steps", [])
        for step in intermediate_steps:
            if isinstance(step, list) and len(step) >= 2:
                action, observation = step[0], step[1]
                actions.append({
                    "type": "tool_call",
                    "tool": action.tool,
                    "input": action.tool_input,
                    "result": observation
                })
        
        return actions
    
    def _update_memory(self, context: AgentContext, response: Dict[str, Any]):
        """Update conversation memory with new exchange."""
        try:
            # Add to memory
            self.memory.chat_memory.add_user_message(context.message)
            self.memory.chat_memory.add_ai_message(response["response"])
            
            # Update session in database
            self._update_session_in_db(context, response)
            
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
    
    def _update_session_in_db(self, context: AgentContext, response: Dict[str, Any]):
        """Update chat session in database."""
        try:
            db = next(get_db())
            
            # Get or create user
            user = db.query(User).filter(User.phone_number == context.user_id).first()
            if not user:
                user = User(
                    phone_number=context.user_id,
                    name=f"User_{context.user_id[-4:]}",
                    status="active"
                )
                db.add(user)
                db.commit()
            
            # Get or create chat session
            session = db.query(ChatSession).filter(
                ChatSession.user_id == user.id,
                ChatSession.is_active == True
            ).first()
            
            if not session:
                session = ChatSession(
                    user_id=user.id,
                    session_data={},
                    current_step="greeting",
                    is_active=True
                )
                db.add(session)
            
            # Update session data
            session_data = session.session_data or {}
            session_data.update({
                "last_message": context.message,
                "last_response": response["response"],
                "last_timestamp": context.timestamp.isoformat(),
                "actions_taken": response.get("actions", [])
            })
            
            session.session_data = session_data
            session.updated_at = datetime.now()
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating session in database: {e}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and capabilities."""
        GEMINI_MODEL = "gemini-1.5-pro"
        
        return {
            "agent_type": "core_agentic_ai",
            "llm_model": GEMINI_MODEL,
            "tools_count": len(self.tools),
            "memory_type": "conversation_buffer_window",
            "capabilities": [
                "autonomous_reasoning",
                "database_access",
                "payment_processing",
                "vector_search",
                "ai_tutoring",
                "conversation_memory"
            ],
            "status": "active"
        }
    
    def reset_conversation(self, user_id: str):
        """Reset conversation for a specific user."""
        try:
            # Clear memory for this user
            # Note: This is a simplified approach - in production, you'd want user-specific memory
            self.memory.clear()
            
            # Update database session
            db = next(get_db())
            user = db.query(User).filter(User.phone_number == user_id).first()
            if user:
                session = db.query(ChatSession).filter(
                    ChatSession.user_id == user.id,
                    ChatSession.is_active == True
                ).first()
                if session:
                    session.is_active = False
                    db.commit()
            
            logger.info(f"Reset conversation for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error resetting conversation for user {user_id}: {e}")

# Global instance
core_agent = CoreAgent()
