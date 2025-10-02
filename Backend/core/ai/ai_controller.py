"""
AI Communication Controller for Isabi WhatsApp Bot
Integrates with PromptManager to control Gemini AI communication flow
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from .prompt_manager import prompt_manager

logger = logging.getLogger(__name__)

class AIController:
    """
    Controls AI communication flow and response generation using Gemini AI
    Integrates with PromptManager for dynamic prompt control
    """
    
    def __init__(self, gemini_model=None):
        self.model = gemini_model
        self.prompt_manager = prompt_manager
        self.conversation_context = {}
        
    def generate_response(self, user_message: str, user_id: str, 
                         chat_history: List[Dict] = None, 
                         products_context: str = None,
                         current_stage: str = "greeting") -> Tuple[str, List[str]]:
        """
        Generate AI response using Gemini with controlled prompts
        
        Args:
            user_message: User's input message
            user_id: User's phone number/ID
            chat_history: Previous conversation history
            products_context: Available products context
            current_stage: Current conversation stage
            
        Returns:
            Tuple of (response_text, suggestion_buttons)
        """
        
        if not self.model:
            return self._generate_fallback_response(user_message, current_stage)
        
        try:
            # Determine conversation stage
            stage = self._determine_conversation_stage(user_message, current_stage)
            
            # Get stage-specific prompt
            stage_prompt = self._build_stage_prompt(stage, user_message, {
                "user_id": user_id,
                "chat_history": chat_history or [],
                "products_context": products_context or "",
                "current_stage": current_stage
            })
            
            # Generate response using Gemini
            response_text = self._generate_gemini_response(stage_prompt)
            
            # Get suggestion buttons for the stage
            buttons = self.prompt_manager.get_suggestion_buttons(stage)
            
            # Apply response formatting rules
            response_text = self._apply_formatting_rules(response_text, stage)
            
            # Update conversation context
            self._update_conversation_context(user_id, stage, user_message, response_text)
            
            logger.info(f"🤖 AI Response generated for stage '{stage}': {response_text[:100]}...")
            logger.info(f"🔘 Suggestion buttons: {buttons}")
            
            return response_text, buttons
            
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
            return self._generate_fallback_response(user_message, current_stage)
    
    def _determine_conversation_stage(self, user_message: str, current_stage: str) -> str:
        """
        Determine the appropriate conversation stage based on user message
        
        Args:
            user_message: User's message
            current_stage: Current conversation stage
            
        Returns:
            Determined conversation stage
        """
        message_lower = user_message.lower()
        conversation_flow = self.prompt_manager.conversation_stages
        
        # Check for stage-specific triggers
        for stage, config in conversation_flow.items():
            triggers = config.get("triggers", [])
            for trigger in triggers:
                if trigger in message_lower:
                    logger.info(f"🎯 Stage transition: {current_stage} → {stage} (trigger: '{trigger}')")
                    return stage
        
        # Default to current stage if no triggers match
        return current_stage
    
    def _build_stage_prompt(self, stage: str, user_message: str, context: Dict[str, Any]) -> str:
        """
        Build comprehensive prompt for the conversation stage
        
        Args:
            stage: Conversation stage
            user_message: User's message
            context: Additional context
            
        Returns:
            Formatted prompt string
        """
        # Get system prompt
        system_prompt = self.prompt_manager.get_system_prompt(context)
        
        # Get stage-specific prompt
        stage_prompt = self.prompt_manager.get_stage_prompt(stage, user_message, context)
        
        # Combine prompts
        full_prompt = f"""{system_prompt}

CURRENT CONVERSATION:
Stage: {stage}
User Message: "{user_message}"

{stage_prompt}

IMPORTANT INSTRUCTIONS:
1. Respond naturally and conversationally
2. Follow the conversation flow for stage: {stage}
3. Use appropriate emojis and formatting
4. Provide helpful product recommendations
5. Ask clarifying questions when needed
6. Keep response concise but informative
7. Include relevant suggestion buttons in your response

Generate your response now:"""
        
        return full_prompt
    
    def _generate_gemini_response(self, prompt: str) -> str:
        """
        Generate response using Gemini AI
        
        Args:
            prompt: Formatted prompt for Gemini
            
        Returns:
            Generated response text
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"❌ Error generating Gemini response: {e}")
            return "I'm here to help you find amazing digital products! What are you looking for?"
    
    def _apply_formatting_rules(self, response_text: str, stage: str) -> str:
        """
        Apply formatting rules to the response
        
        Args:
            response_text: Generated response text
            stage: Current conversation stage
            
        Returns:
            Formatted response text
        """
        behavior_rules = self.prompt_manager.get_behavior_rules()
        
        # Apply length constraints
        max_length = behavior_rules.get("max_response_length", 500)
        min_length = behavior_rules.get("min_response_length", 50)
        
        if len(response_text) > max_length:
            response_text = response_text[:max_length-3] + "..."
        elif len(response_text) < min_length:
            response_text += "\n\nHow can I help you further?"
        
        # Ensure proper formatting
        if not response_text.endswith(('.', '!', '?')):
            response_text += "!"
        
        return response_text
    
    def _generate_fallback_response(self, user_message: str, current_stage: str) -> Tuple[str, List[str]]:
        """
        Generate fallback response when Gemini is not available
        
        Args:
            user_message: User's message
            current_stage: Current conversation stage
            
        Returns:
            Tuple of (response_text, suggestion_buttons)
        """
        message_lower = user_message.lower()
        
        # Simple rule-based responses
        if any(greeting in message_lower for greeting in ['hi', 'hello', 'hey']):
            response = "Hello! I'm iSabi, your digital products assistant! 👋\n\nI can help you find amazing products. What are you looking for?"
            buttons = ["View Products", "Get Help", "Contact Support"]
        elif any(word in message_lower for word in ['product', 'buy', 'shop']):
            response = "Great! I have many digital products available. What type of product interests you?"
            buttons = ["AI Courses", "Digital Items", "Show All"]
        elif any(word in message_lower for word in ['help', 'support']):
            response = "I'm here to help! What kind of support do you need?"
            buttons = ["Technical Support", "Billing Help", "General Questions"]
        else:
            response = self.prompt_manager.get_fallback_response("unclear_input")
            buttons = ["View Products", "Get Help", "Contact Support"]
        
        logger.info(f"�� Fallback response generated: {response[:100]}...")
        return response, buttons
    
    def _update_conversation_context(self, user_id: str, stage: str, 
                                   user_message: str, bot_response: str):
        """
        Update conversation context for the user
        
        Args:
            user_id: User's ID
            stage: Current stage
            user_message: User's message
            bot_response: Bot's response
        """
        if user_id not in self.conversation_context:
            self.conversation_context[user_id] = {
                "current_stage": stage,
                "message_count": 0,
                "last_interaction": datetime.now().isoformat(),
                "conversation_history": []
            }
        
        # Update context
        self.conversation_context[user_id]["current_stage"] = stage
        self.conversation_context[user_id]["message_count"] += 1
        self.conversation_context[user_id]["last_interaction"] = datetime.now().isoformat()
        
        # Add to conversation history
        self.conversation_context[user_id]["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "stage": stage
        })
        
        # Keep only last 10 interactions
        if len(self.conversation_context[user_id]["conversation_history"]) > 10:
            self.conversation_context[user_id]["conversation_history"] = \
                self.conversation_context[user_id]["conversation_history"][-10:]
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get conversation context for a user
        
        Args:
            user_id: User's ID
            
        Returns:
            User's conversation context
        """
        return self.conversation_context.get(user_id, {
            "current_stage": "greeting",
            "message_count": 0,
            "last_interaction": datetime.now().isoformat(),
            "conversation_history": []
        })
    
    def update_prompt_config(self, new_config: Dict[str, Any]):
        """
        Update prompt configuration dynamically
        
        Args:
            new_config: New configuration to apply
        """
        self.prompt_manager.update_prompts(new_config)
        logger.info("✅ Prompt configuration updated successfully")
    
    def get_conversation_analytics(self) -> Dict[str, Any]:
        """
        Get analytics about conversations
        
        Returns:
            Conversation analytics
        """
        total_users = len(self.conversation_context)
        total_messages = sum(
            user_data["message_count"] 
            for user_data in self.conversation_context.values()
        )
        
        stage_distribution = {}
        for user_data in self.conversation_context.values():
            stage = user_data["current_stage"]
            stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
        
        return {
            "total_active_users": total_users,
            "total_messages_processed": total_messages,
            "stage_distribution": stage_distribution,
            "average_messages_per_user": total_messages / total_users if total_users > 0 else 0
        }

# Global instance
ai_controller = AIController()
