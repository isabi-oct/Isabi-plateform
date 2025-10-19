#!/usr/bin/env python3
"""
Test Gemini 2.0 Flash Experimental Integration
"""

import os
from dotenv import load_dotenv
from Backend.services.ai_service import ai_service

load_dotenv()

def test_gemini_2_0():
    """Test the Gemini 2.0 Flash Experimental model"""
    print("🧪 Testing Gemini 2.0 Flash Experimental Integration")
    print("=" * 60)
    
    # Test 1: Basic conversation
    print("\n🔸 Test 1: Basic Conversation")
    response = ai_service.generate_conversation_response(
        user_message="Hi, I'm interested in learning Python programming",
        user_profile={"interests": ["programming", "python"], "conversation_count": 1}
    )
    print(f"Response: {response}")
    
    # Test 2: Product inquiry
    print("\n🔸 Test 2: Product Inquiry")
    response = ai_service.generate_answer(
        question="What Python courses do you have available?",
        context_documents=[
            "Python Programming Course - Comprehensive beginner to advanced course",
            "AI Training Course - Machine learning fundamentals",
            "Web Development Course - Django and Flask frameworks"
        ]
    )
    print(f"Response: {response}")
    
    # Test 3: Product recommendation
    print("\n🔸 Test 3: Product Recommendation")
    products = [
        {"name": "Python Basics", "description": "Learn Python from scratch", "price": 29.99},
        {"name": "AI Fundamentals", "description": "Introduction to AI and ML", "price": 49.99},
        {"name": "Web Development", "description": "Build web applications", "price": 39.99}
    ]
    response = ai_service.generate_product_recommendation(
        user_interests=["python", "programming", "beginner"],
        available_products=products
    )
    print(f"Response: {response}")
    
    print("\n✅ Gemini 2.0 Flash Experimental tests completed!")

if __name__ == "__main__":
    test_gemini_2_0()
