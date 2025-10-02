"""
AI Module for Isabi WhatsApp Bot
Contains prompt management and AI communication control systems
"""

from .prompt_manager import PromptManager, prompt_manager
from .ai_controller import AIController, ai_controller

__all__ = [
    'PromptManager',
    'prompt_manager', 
    'AIController',
    'ai_controller'
]

__version__ = "1.0.0"
