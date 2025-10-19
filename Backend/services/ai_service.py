import google.generativeai as genai
from Backend.config.settings import settings
from Database.VectorDB.gcp_vector_client import gcp_vector_client
from typing import List, Dict, Any
import json

# Configure Gemini API
genai.configure(api_key=settings.gemini_api_key)

class AIService:
    def __init__(self):
        # Use Gemini 2.0 Flash Experimental for enhanced conversation capabilities
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("🤖 Gemini 2.0 Flash Experimental model initialized")
    
    def generate_answer(self, question: str, product_id: int = None, context_documents: List[str] = None,
    user_context: Dict = None) -> str:
        """Generate an answer to a product-related question using Gemini 2.0 Flash"""
        try:
            # Build context from various sources
            context_parts = []
            
            if context_documents:
                context_parts.append("Product Knowledge Base:")
                context_parts.extend(context_documents)
            
            if user_context:
                context_parts.append(f"User Context: {json.dumps(user_context, indent=2)}")
            
            context = "\n".join(context_parts) if context_parts else "No specific context available."
            
            prompt = f"""
            You are an advanced AI assistant for the Isabi platform,
    specializing in product support and sales assistance.
            
            Context Information:
            {context}
            
            User Question: {question}
            
            Instructions:
            1. Provide helpful, accurate, and detailed answers
            2. If discussing products, be specific about features and benefits
            3. Maintain a friendly, professional tone
            4. If you don't have enough information, ask clarifying questions
            5. Suggest related products or services when appropriate
            6. Keep responses concise but informative (2-3 sentences max for WhatsApp)
            
            Please provide a helpful response:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"I apologize, but I'm having trouble processing your question right now. Please try again later."
    
    def generate_conversation_response(self, user_message: str, conversation_history: List[Dict] = None,
    user_profile: Dict = None) -> str:
        """Generate a conversational response using Gemini 2.0 Flash"""
        try:
            # Build conversation context
            history_context = ""
            if conversation_history:
                recent_messages = conversation_history[-5:]  # Last 5 messages
                history_context = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                    for msg in recent_messages
                ])
            
            user_context = ""
            if user_profile:
                user_context = f"User Profile: {json.dumps(user_profile, indent=2)}"
            
            prompt = f"""
            You are an AI sales assistant for the Isabi platform. You help users discover and purchase digital products and AI training courses.
            
            {user_context}
            
            Recent Conversation:
            {history_context}
            
            Current User Message: {user_message}
            
            Instructions:
            1. Respond naturally and conversationally
            2. Help users find products that match their needs
            3. Provide product recommendations when appropriate
            4. Answer questions about products, pricing, and features
            5. Guide users through the purchase process
            6. Be helpful, friendly, and professional
            7. Keep responses concise (1-2 sentences for WhatsApp)
            8. Use emojis sparingly and appropriately
            
            Respond to the user's message:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "I'm here to help! What can I assist you with today?"
    
    def generate_product_recommendation(self, user_interests: List[str], available_products: List[Dict]) -> str:
        """Generate product recommendations based on user interests"""
        try:
            products_info = "\n".join([
                f"- {p.get('name', 'Unknown')}: {p.get('description', 'No description')} (${p.get('price', 0)})"
                for p in available_products
            ])
            
            interests_text = ", ".join(user_interests)
            
            prompt = f"""
            Based on the user's interests: {interests_text}
            
            Available Products:
            {products_info}
            
            Recommend 2-3 products that best match their interests. Explain why each product is a good fit.
            Keep the response concise and engaging for WhatsApp.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "I'd be happy to help you find products! What are you interested in learning about?"
    
    def generate_quiz(self, product_id: int, topic: str = None) -> Dict[str, Any]:
        """Generate a quiz question for a product using Gemini 2.0 Flash"""
        try:
            prompt = f"""
            Generate an engaging quiz question about the product with ID {product_id}.
            {f"Focus on the topic: {topic}" if topic else ""}
            
            Return a JSON object with the following structure:
            {{
                "question": "Your quiz question here",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": 0,
                "explanation": "Explanation of the correct answer"
            }}
            
            Make the question educational and relevant to the product.
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse the JSON response
            quiz_data = json.loads(response.text.strip())
            return quiz_data
        except Exception as e:
            return {
                "question": "What is the main feature of this product?",
                "options": ["Feature A", "Feature B", "Feature C", "Feature D"],
                "correct_answer": 0,
                "explanation": "This is a sample quiz question."
            }
    
    def search_product_knowledge(self, product_id: int, query: str) -> List[str]:
        """Search the product's knowledge base using GCP Vector Search"""
        try:
            collection_name = f"product_{product_id}_knowledge"
            results = gcp_vector_client.query_collection(collection_name, query, n_results=3)
            
            if results and "documents" in results:
                return results["documents"][0] if results["documents"] else []
            return []
        except Exception as e:
            print(f"Error searching product knowledge: {e}")
            return []
    
    def add_product_knowledge(self, product_id: int, documents: List[str], metadatas: List[Dict] = None) -> bool:
        """Add knowledge documents to a product's GCP Vector Search database"""
        try:
            collection_name = f"product_{product_id}_knowledge"
            
            # Create collection if it doesn't exist
            gcp_vector_client.create_collection(collection_name)
            
            # Add documents
            ids = gcp_vector_client.add_documents(collection_name, documents, metadatas)
            return len(ids) > 0
        except Exception as e:
            print(f"Error adding product knowledge: {e}")
            return False

# Global instance
ai_service = AIService()
