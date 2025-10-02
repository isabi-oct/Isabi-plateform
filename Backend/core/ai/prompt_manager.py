"""
AI Prompt Management System for Isabi WhatsApp Bot
Controls communication flow, accuracy, and behavior of Gemini AI
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Manages AI prompts and communication flow for the WhatsApp bot.
    Allows dynamic control over bot behavior, accuracy, and conversation flow.
    """
    
    def __init__(self, config_file: str = "Backend/core/ai/prompts_config.json"):
        self.config_file = config_file
        self.prompts = self._load_prompts()
        self.conversation_stages = self._load_conversation_stages()
        self.response_templates = self._load_response_templates()
        
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from configuration file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default prompts if file doesn't exist
                return self._create_default_prompts()
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            return self._create_default_prompts()
    
    def _create_default_prompts(self) -> Dict[str, Any]:
        """Create default prompt configuration"""
        default_prompts = {
            "system_personality": {
                "name": "iSabi",
                "role": "Digital Products Sales Assistant",
                "personality_traits": [
                    "Friendly and professional",
                    "Helpful and knowledgeable",
                    "Patient with customers",
                    "Enthusiastic about products"
                ],
                "communication_style": "Conversational, warm, and engaging",
                "language_preference": "English with appropriate emojis"
            },
            
            "conversation_flow": {
                "greeting": {
                    "triggers": ["hi", "hello", "hey", "start", "begin"],
                    "response_template": "greeting_template",
                    "next_stage": "service_selection",
                    "buttons": ["View Products", "Get Help", "Contact Support"]
                },
                "service_selection": {
                    "triggers": ["product", "buy", "shop", "digital"],
                    "response_template": "service_selection_template",
                    "next_stage": "product_category",
                    "buttons": ["AI Courses", "Digital Items", "Show All"]
                }
            },
            
            "response_templates": {
                "greeting_template": {
                    "template": "Hello! I'm {name}, your {role}! 👋\n\nI'm here to help you find amazing digital products. What can I help you with today?",
                    "variables": ["name", "role"],
                    "tone": "welcoming"
                },
                "service_selection_template": {
                    "template": "Great! 🛍️ I have {product_count} amazing digital products across {category_count} categories.\n\nWhich type of product interests you most?",
                    "variables": ["product_count", "category_count"],
                    "tone": "enthusiastic"
                }
            },
            
            "behavior_rules": {
                "always_ask_clarification": True,
                "provide_multiple_options": True,
                "use_emojis": True,
                "keep_responses_concise": True,
                "max_response_length": 500,
                "min_response_length": 50,
                "suggestion_buttons_count": 3
            },
            
            "fallback_responses": {
                "unclear_input": "I'm not sure I understand. Could you please clarify what you're looking for?",
                "no_products_found": "I couldn't find products matching your criteria. Let me show you some popular options instead.",
                "error_occurred": "I encountered an issue. Please try again or contact support if the problem persists."
            }
        }
        
        # Save default prompts to file
        self._save_prompts(default_prompts)
        return default_prompts
    
    def _load_conversation_stages(self) -> Dict[str, Any]:
        """Load conversation stage configurations"""
        return self.prompts.get("conversation_flow", {})
    
    def _load_response_templates(self) -> Dict[str, Any]:
        """Load response templates"""
        return self.prompts.get("response_templates", {})
    
    def _save_prompts(self, prompts: Dict[str, Any]):
        """Save prompts to configuration file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, indent=2, ensure_ascii=False)
            logger.info(f"Prompts saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving prompts: {e}")
    
    def get_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Generate the main system prompt for Gemini AI"""
        personality = self.prompts.get("system_personality", {})
        behavior_rules = self.prompts.get("behavior_rules", {})
        
        system_prompt = f"""You are {personality.get('name', 'iSabi')}, a {personality.get('role', 'Digital Products Sales Assistant')}.

PERSONALITY TRAITS:
{chr(10).join(f"- {trait}" for trait in personality.get('personality_traits', []))}

COMMUNICATION STYLE:
- {personality.get('communication_style', 'Conversational, warm, and engaging')}
- {personality.get('language_preference', 'English with appropriate emojis')}

BEHAVIOR RULES:
- Always be helpful and professional
- Keep responses between {behavior_rules.get('min_response_length', 50)} and {behavior_rules.get('max_response_length', 500)} characters
- Use emojis appropriately: {behavior_rules.get('use_emojis', True)}
- Provide {behavior_rules.get('suggestion_buttons_count', 3)} suggestion buttons when appropriate

Remember: You are here to help users find the perfect digital products for their needs while providing excellent customer service."""
        
        if context:
            system_prompt += f"\n\nCURRENT CONTEXT:\n{json.dumps(context, indent=2)}"
        
        return system_prompt
    
    def get_stage_prompt(self, stage: str, user_message: str, context: Dict[str, Any] = None) -> str:
        """Get stage-specific prompt for conversation flow"""
        stage_config = self.conversation_stages.get(stage, {})
        template_name = stage_config.get("response_template", "greeting_template")
        template = self.response_templates.get(template_name, {})
        
        prompt = f"""Current conversation stage: {stage}
User message: "{user_message}"

Stage configuration: {json.dumps(stage_config, indent=2)}
Response template: {json.dumps(template, indent=2)}

Generate an appropriate response following the template and stage configuration."""
        
        if context:
            prompt += f"\n\nAdditional context: {json.dumps(context, indent=2)}"
        
        return prompt
    
    def get_fallback_response(self, error_type: str = "unclear_input") -> str:
        """Get fallback response for error situations"""
        fallback_responses = self.prompts.get("fallback_responses", {})
        return fallback_responses.get(error_type, "I'm here to help! What can I assist you with?")
    
    def update_prompts(self, new_prompts: Dict[str, Any]):
        """Update prompts configuration"""
        self.prompts.update(new_prompts)
        self._save_prompts(self.prompts)
        logger.info("Prompts updated successfully")
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current prompt configuration"""
        return self.prompts.copy()
    
    def get_accuracy_settings(self) -> Dict[str, Any]:
        """Get accuracy settings for product matching"""
        return self.prompts.get("accuracy_settings", {})
    
    def get_behavior_rules(self) -> Dict[str, Any]:
        """Get behavior rules for AI responses"""
        return self.prompts.get("behavior_rules", {})
    
    def format_response_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Format a response template with variables"""
        template_config = self.response_templates.get(template_name, {})
        template = template_config.get("template", "Hello! How can I help you?")
        
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.error(f"Missing variable {e} for template {template_name}")
            return template
    
    def get_suggestion_buttons(self, stage: str) -> List[str]:
        """Get suggestion buttons for a conversation stage"""
        stage_config = self.conversation_stages.get(stage, {})
        return stage_config.get("buttons", ["Get Help", "Contact Support"])

# Global instance
prompt_manager = PromptManager()
