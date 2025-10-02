# Enhanced AI Conversation Service with Database Integration
import google.generativeai as genai
import os
import logging
import psycopg2
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv('Config/.env')
logger = logging.getLogger(__name__)

class AIConversationService:
    def __init__(self):
        """Initialize AI conversation service with Gemini and database integration"""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.database_url = os.getenv("DATABASE_URL")
        
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("🤖 Enhanced Gemini AI conversation service initialized")
        else:
            logger.warning("⚠️ No Gemini API key found - using fallback responses")
            self.model = None
    
    async def process_message(self, message: str, user_id: str, context: Dict = None) -> Dict[str, Any]:
        """Process user message and return AI response with suggestions"""
        try:
            logger.info(f"🧠 Processing message from {user_id}: {message}")
            
            # Get products from database
            products = await self._get_products_from_database()
            
            if self.model:
                # Use Gemini AI for response
                response_text = await self._generate_gemini_response(message, user_id, products, context)
            else:
                # Use fallback responses
                response_text = self._generate_fallback_response(message, products)
            
            # Generate suggestion buttons based on message intent
            suggestions = await self._generate_suggestions(message, products)
            
            result = {
                "text": response_text,
                "suggestions": suggestions,
                "products": products[:3] if products else []  # Include top 3 products
            }
            
            logger.info(f"🤖 AI Response: {response_text}")
            logger.info(f"🔘 Suggestions: {suggestions}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "text": "Sorry, I'm having trouble understanding. Could you please rephrase your question?",
                "suggestions": ["View Products", "Get Help", "Contact Support"],
                "products": []
            }
    
    async def _get_products_from_database(self) -> List[Dict]:
        """Get products from database"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT product_id, product_name, price, status, created_at
                FROM products 
                WHERE status = 'active' 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            products = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            product_list = []
            for product in products:
                product_list.append({
                    "id": product[0],
                    "name": product[1],
                    "price": product[2],
                    "status": product[3],
                    "created_at": product[4]
                })
            
            logger.info(f"📊 Retrieved {len(product_list)} products from database")
            return product_list
            
        except Exception as e:
            logger.error(f"Error getting products from database: {e}")
            return []
    
    async def _generate_gemini_response(self, message: str, user_id: str, products: List[Dict], context: Dict = None) -> str:
        """Generate response using Gemini AI with product context"""
        try:
            # Build product context
            product_context = ""
            if products:
                product_context = "Available Products:\n"
                for product in products[:5]:  # Include top 5 products
                    product_context += f"- {product['name']} (${product['price']})\n"
            
            # Build context prompt
            context_prompt = self._build_context_prompt(user_id, context)
            
            # Create the full prompt
            full_prompt = f"""
            You are Isabi, an AI assistant for a WhatsApp sales bot. You help users with:
            - Product information and recommendations
            - Course details and learning paths
            - Payment and order assistance
            - General questions about our services
            
            {product_context}
            
            Context: {context_prompt}
            
            User message: {message}
            
            Respond in a friendly, helpful, and professional manner. Keep responses concise but informative.
            If the user asks about products, provide specific information about available products.
            If they need help with orders or payments, guide them through the process.
            Always mention specific product names and prices when relevant.
            """
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return self._generate_fallback_response(message, products)
    
    async def _generate_suggestions(self, message: str, products: List[Dict]) -> List[str]:
        """Generate suggestion buttons based on message intent"""
        message_lower = message.lower()
        
        # Default suggestions
        suggestions = ["View Products", "Get Help", "Contact Support"]
        
        # Product-related suggestions
        if any(word in message_lower for word in ["product", "course", "learn", "education", "buy", "purchase"]):
            suggestions = ["View All Products", "Course Details", "Pricing Info", "Get Help"]
        
        # Pricing-related suggestions
        elif any(word in message_lower for word in ["price", "cost", "payment", "buy", "order"]):
            suggestions = ["View Pricing", "Payment Options", "Order Now", "Get Help"]
        
        # Help-related suggestions
        elif any(word in message_lower for word in ["help", "support", "problem", "issue"]):
            suggestions = ["Product Help", "Payment Help", "Contact Support", "FAQ"]
        
        # Greeting suggestions
        elif any(word in message_lower for word in ["hello", "hi", "hey", "start"]):
            suggestions = ["View Products", "Course Info", "Pricing", "Get Help"]
        
        return suggestions
    
    def _build_context_prompt(self, user_id: str, context: Dict = None) -> str:
        """Build context prompt for AI"""
        context_info = f"User ID: {user_id}"
        
        if context:
            if context.get("conversation_history"):
                context_info += f"\nRecent conversation: {context['conversation_history']}"
            if context.get("user_preferences"):
                context_info += f"\nUser preferences: {context['user_preferences']}"
            if context.get("current_product"):
                context_info += f"\nCurrent product: {context['current_product']}"
        
        return context_info
    
    def _generate_fallback_response(self, message: str, products: List[Dict]) -> str:
        """Generate fallback response when AI is not available"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["hello", "hi", "hey", "start"]):
            if products:
                product_list = "\n".join([f"- {p['name']} (${p['price']})" for p in products[:3]])
                return f"Hello! Welcome to Isabi! 🤖\n\nI'm here to help you with our products and services. Here are some of our popular products:\n\n{product_list}\n\nHow can I assist you today?"
            else:
                return "Hello! Welcome to Isabi! 🤖 I'm here to help you with our products and services. How can I assist you today?"
        
        elif any(word in message_lower for word in ["product", "course", "learn", "education"]):
            if products:
                product_list = "\n".join([f"- {p['name']} (${p['price']})" for p in products[:3]])
                return f"Great! We offer various digital products and courses. Here are some popular options:\n\n{product_list}\n\nWhat specific topic or skill are you interested in learning about?"
            else:
                return "Great! We offer various digital products and courses. What specific topic or skill are you interested in learning about?"
        
        elif any(word in message_lower for word in ["price", "cost", "payment", "buy"]):
            if products:
                product_list = "\n".join([f"- {p['name']}: ${p['price']}" for p in products[:3]])
                return f"I'd be happy to help you with pricing information! Here are some of our products:\n\n{product_list}\n\nWhich product are you interested in?"
            else:
                return "I'd be happy to help you with pricing information! Could you tell me which product or course you're interested in?"
        
        elif any(word in message_lower for word in ["help", "support", "problem"]):
            return "I'm here to help! What specific issue or question do you have? I can assist with product information, orders, payments, or general questions."
        
        elif any(word in message_lower for word in ["thank", "thanks"]):
            return "You're welcome! Is there anything else I can help you with today?"
        
        else:
            if products:
                product_list = "\n".join([f"- {p['name']} (${p['price']})" for p in products[:2]])
                return f"Thanks for your message! I'm here to help you with our products and services. Here are some popular options:\n\n{product_list}\n\nYou can ask me about courses, pricing, orders, or anything else you need assistance with."
            else:
                return "Thanks for your message! I'm here to help you with our products and services. You can ask me about courses, pricing, orders, or anything else you need assistance with."

# Create global instance
ai_conversation_service = AIConversationService()
