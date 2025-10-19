#!/usr/bin/env python3
"""
Test script for the Agentic AI system

This script tests the core functionality of the agentic AI system
without requiring a full WhatsApp webhook setup.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.core_agent import CoreAgent, AgentContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agentic_system():
    """Test the agentic AI system with sample messages."""
    
    print("🤖 Testing Agentic AI System")
    print("=" * 50)
    
    try:
        # Initialize the core agent
        print("Initializing Core Agent...")
        agent = CoreAgent()
        print("✅ Core Agent initialized successfully")
        
        # Test messages
        test_messages = [
            "Hello, I'm interested in AI courses",
            "I want to buy a digital product",
            "What AI tutoring products do you have?",
            "I need help with my order",
            "Show me your best selling products"
        ]
        
        phone_number = "+1234567890"
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📱 Test {i}: {message}")
            print("-" * 30)
            
            # Create agent context
            context = AgentContext(
                user_id=phone_number,
                message=message,
                conversation_history=[],
                platform="test",
                timestamp=datetime.now()
            )
            
            # Process message
            try:
                response = await agent.process_message(context)
                
                if response.get("success"):
                    print(f"✅ Response: {response['response']}")
                    
                    # Show actions taken
                    actions = response.get("actions", [])
                    if actions:
                        print(f"🔧 Actions taken: {len(actions)}")
                        for action in actions:
                            print(f"   - {action.get('type', 'unknown')}: {action.get('tool', 'unknown')}")
                    
                    # Show metadata
                    metadata = response.get("metadata", {})
                    if metadata:
                        print(f"📊 Metadata: {metadata}")
                else:
                    print(f"❌ Error: {response.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error processing message: {e}")
            
            print()
        
        # Test agent status
        print("📊 Agent Status:")
        print("-" * 20)
        status = agent.get_agent_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Agentic AI System test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing agentic system: {e}")
        logger.error(f"Test failed: {e}")

async def test_simple_conversation():
    """Test a simple conversation flow."""
    
    print("\n🔄 Testing Simple Conversation Flow")
    print("=" * 50)
    
    try:
        agent = CoreAgent()
        phone_number = "+1234567890"
        
        # Simulate a conversation
        conversation = [
            "Hi, I'm looking for AI courses",
            "What's the price of your best AI course?",
            "I want to buy it",
            "How do I pay?"
        ]
        
        conversation_history = []
        
        for i, message in enumerate(conversation, 1):
            print(f"\n👤 User: {message}")
            
            context = AgentContext(
                user_id=phone_number,
                message=message,
                conversation_history=conversation_history,
                platform="test",
                timestamp=datetime.now()
            )
            
            response = await agent.process_message(context)
            
            if response.get("success"):
                bot_response = response['response']
                print(f"🤖 Bot: {bot_response}")
                
                # Add to conversation history
                conversation_history.append({
                    "user_message": message,
                    "bot_response": bot_response,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        print("\n✅ Conversation flow test completed!")
        
    except Exception as e:
        print(f"❌ Error in conversation test: {e}")

if __name__ == "__main__":
    print("🚀 Starting Agentic AI System Tests")
    print("=" * 60)
    
    # Run tests
    asyncio.run(test_agentic_system())
    asyncio.run(test_simple_conversation())
    
    print("\n🎉 All tests completed!")
    print("\nTo test with the full API:")
    print("1. Start the server: uvicorn api.main:app --reload")
    print("2. Test endpoint: POST /whatsapp/agentic/test")
    print("3. Check status: GET /whatsapp/agentic/status")
