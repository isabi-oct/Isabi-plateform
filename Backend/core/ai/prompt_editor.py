"""
Prompt Editor Utility for Isabi WhatsApp Bot
Allows easy editing and management of AI prompts and communication flow
"""

import json
import os
from typing import Dict, Any, List
from .prompt_manager import prompt_manager

class PromptEditor:
    """
    Utility class for editing and managing AI prompts
    Provides easy-to-use methods for customizing bot behavior
    """
    
    def __init__(self):
        self.prompt_manager = prompt_manager
    
    def update_personality(self, name: str = None, role: str = None, 
                          traits: List[str] = None, style: str = None):
        """
        Update bot personality settings
        
        Args:
            name: Bot's name
            role: Bot's role description
            traits: List of personality traits
            style: Communication style
        """
        personality_updates = {}
        
        if name:
            personality_updates["name"] = name
        if role:
            personality_updates["role"] = role
        if traits:
            personality_updates["personality_traits"] = traits
        if style:
            personality_updates["communication_style"] = style
        
        if personality_updates:
            self.prompt_manager.prompts["system_personality"].update(personality_updates)
            self.prompt_manager._save_prompts(self.prompt_manager.prompts)
            print(f"✅ Personality updated: {personality_updates}")
    
    def add_conversation_stage(self, stage_name: str, triggers: List[str], 
                              template: str, buttons: List[str], next_stage: str = None):
        """
        Add a new conversation stage
        
        Args:
            stage_name: Name of the stage
            triggers: List of trigger words/phrases
            template: Response template name
            buttons: List of suggestion buttons
            next_stage: Next stage in flow
        """
        new_stage = {
            "triggers": triggers,
            "response_template": template,
            "next_stage": next_stage or "greeting",
            "buttons": buttons,
            "description": f"Custom stage: {stage_name}"
        }
        
        self.prompt_manager.prompts["conversation_flow"][stage_name] = new_stage
        self.prompt_manager._save_prompts(self.prompt_manager.prompts)
        print(f"✅ Added conversation stage: {stage_name}")
    
    def update_response_template(self, template_name: str, template: str, 
                                variables: List[str] = None, tone: str = None):
        """
        Update a response template
        
        Args:
            template_name: Name of the template
            template: Template string with {variables}
            variables: List of variable names
            tone: Tone of the response
        """
        template_config = {
            "template": template,
            "variables": variables or [],
            "tone": tone or "neutral",
            "max_length": 500
        }
        
        self.prompt_manager.prompts["response_templates"][template_name] = template_config
        self.prompt_manager._save_prompts(self.prompt_manager.prompts)
        print(f"✅ Updated response template: {template_name}")
    
    def update_behavior_rules(self, **rules):
        """
        Update behavior rules
        
        Args:
            **rules: Key-value pairs of behavior rules to update
        """
        self.prompt_manager.prompts["behavior_rules"].update(rules)
        self.prompt_manager._save_prompts(self.prompt_manager.prompts)
        print(f"✅ Updated behavior rules: {rules}")
    
    def update_fallback_responses(self, **responses):
        """
        Update fallback responses
        
        Args:
            **responses: Key-value pairs of fallback responses
        """
        self.prompt_manager.prompts["fallback_responses"].update(responses)
        self.prompt_manager._save_prompts(self.prompt_manager.prompts)
        print(f"✅ Updated fallback responses: {responses}")
    
    def update_accuracy_settings(self, **settings):
        """
        Update accuracy settings for product matching
        
        Args:
            **settings: Key-value pairs of accuracy settings
        """
        self.prompt_manager.prompts["accuracy_settings"].update(settings)
        self.prompt_manager._save_prompts(self.prompt_manager.prompts)
        print(f"✅ Updated accuracy settings: {settings}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get current prompt configuration
        
        Returns:
            Current configuration dictionary
        """
        return self.prompt_manager.prompts.copy()
    
    def reset_to_defaults(self):
        """Reset all prompts to default configuration"""
        default_prompts = self.prompt_manager._create_default_prompts()
        self.prompt_manager.prompts = default_prompts
        self.prompt_manager._save_prompts(default_prompts)
        print("✅ Reset to default configuration")
    
    def export_config(self, filename: str = None):
        """
        Export current configuration to JSON file
        
        Args:
            filename: Output filename (optional)
        """
        if not filename:
            filename = f"prompts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.prompt_manager.prompts, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Configuration exported to: {filename}")
    
    def import_config(self, filename: str):
        """
        Import configuration from JSON file
        
        Args:
            filename: Input filename
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            self.prompt_manager.prompts = imported_config
            self.prompt_manager._save_prompts(imported_config)
            print(f"✅ Configuration imported from: {filename}")
        except Exception as e:
            print(f"❌ Error importing configuration: {e}")
    
    def preview_response(self, template_name: str, variables: Dict[str, Any] = None):
        """
        Preview how a response template would look with given variables
        
        Args:
            template_name: Name of the template
            variables: Variables to substitute
        """
        variables = variables or {}
        try:
            response = self.prompt_manager.format_response_template(template_name, variables)
            print(f"📝 Preview for '{template_name}':")
            print(f"{response}")
            print("-" * 50)
        except Exception as e:
            print(f"❌ Error previewing template: {e}")
    
    def list_available_templates(self):
        """List all available response templates"""
        templates = self.prompt_manager.prompts.get("response_templates", {})
        print("📋 Available Response Templates:")
        for name, config in templates.items():
            print(f"  • {name}: {config.get('tone', 'neutral')} tone")
        print("-" * 50)
    
    def list_conversation_stages(self):
        """List all conversation stages"""
        stages = self.prompt_manager.prompts.get("conversation_flow", {})
        print("🔄 Conversation Stages:")
        for name, config in stages.items():
            triggers = ", ".join(config.get("triggers", [])[:3])
            print(f"  • {name}: {triggers}...")
        print("-" * 50)

# Example usage functions
def quick_personality_update():
    """Quick example of updating bot personality"""
    editor = PromptEditor()
    editor.update_personality(
        name="iSabi Pro",
        role="Premium Digital Products Consultant",
        traits=["Expert", "Professional", "Knowledgeable", "Efficient"],
        style="Professional, expert, and solution-focused"
    )

def quick_template_update():
    """Quick example of updating a response template"""
    editor = PromptEditor()
    editor.update_response_template(
        template_name="greeting_template",
        template="Welcome to iSabi Pro! 🚀\n\nI'm your premium digital products consultant. I specialize in finding the perfect products to accelerate your success.\n\nWhat goals are you looking to achieve today?",
        variables=["name", "role"],
        tone="premium"
    )

def quick_behavior_update():
    """Quick example of updating behavior rules"""
    editor = PromptEditor()
    editor.update_behavior_rules(
        max_response_length=600,
        min_response_length=100,
        use_emojis=True,
        provide_multiple_options=True,
        suggestion_buttons_count=4
    )

if __name__ == "__main__":
    # Interactive prompt editor
    editor = PromptEditor()
    
    print("🤖 Isabi Prompt Editor")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Update personality")
        print("2. Update response template")
        print("3. Update behavior rules")
        print("4. Update fallback responses")
        print("5. Preview template")
        print("6. List templates")
        print("7. List stages")
        print("8. Export config")
        print("9. Reset to defaults")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-9): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            name = input("Bot name (optional): ").strip() or None
            role = input("Bot role (optional): ").strip() or None
            traits_input = input("Personality traits (comma-separated, optional): ").strip()
            traits = [t.strip() for t in traits_input.split(",")] if traits_input else None
            style = input("Communication style (optional): ").strip() or None
            editor.update_personality(name, role, traits, style)
        elif choice == "2":
            template_name = input("Template name: ").strip()
            template = input("Template text: ").strip()
            variables_input = input("Variables (comma-separated, optional): ").strip()
            variables = [v.strip() for v in variables_input.split(",")] if variables_input else None
            tone = input("Tone (optional): ").strip() or None
            editor.update_response_template(template_name, template, variables, tone)
        elif choice == "3":
            print("Enter behavior rules (key=value, one per line, empty line to finish):")
            rules = {}
            while True:
                rule_input = input("Rule: ").strip()
                if not rule_input:
                    break
                if "=" in rule_input:
                    key, value = rule_input.split("=", 1)
                    try:
                        # Try to convert to appropriate type
                        if value.lower() in ["true", "false"]:
                            rules[key.strip()] = value.lower() == "true"
                        elif value.isdigit():
                            rules[key.strip()] = int(value)
                        else:
                            rules[key.strip()] = value.strip()
                    except:
                        rules[key.strip()] = value.strip()
            if rules:
                editor.update_behavior_rules(**rules)
        elif choice == "4":
            print("Enter fallback responses (key=value, one per line, empty line to finish):")
            responses = {}
            while True:
                response_input = input("Response: ").strip()
                if not response_input:
                    break
                if "=" in response_input:
                    key, value = response_input.split("=", 1)
                    responses[key.strip()] = value.strip()
            if responses:
                editor.update_fallback_responses(**responses)
        elif choice == "5":
            template_name = input("Template name: ").strip()
            variables_input = input("Variables (key=value, comma-separated, optional): ").strip()
            variables = {}
            if variables_input:
                for pair in variables_input.split(","):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        variables[key.strip()] = value.strip()
            editor.preview_response(template_name, variables)
        elif choice == "6":
            editor.list_available_templates()
        elif choice == "7":
            editor.list_conversation_stages()
        elif choice == "8":
            filename = input("Export filename (optional): ").strip() or None
            editor.export_config(filename)
        elif choice == "9":
            confirm = input("Are you sure? This will reset all prompts to defaults (y/N): ").strip().lower()
            if confirm == "y":
                editor.reset_to_defaults()
        else:
            print("Invalid choice. Please try again.")
