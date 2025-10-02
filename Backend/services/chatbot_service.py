from sqlalchemy.orm import Session
from app.models.database.models import User, Product, Order, ChatSession, OrderStatus, ProductType
from app.services.whatsapp_service import whatsapp_service
from app.services.payment_service import payment_service
from app.services.ai_service import ai_service
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

class ChatbotService:
    def __init__(self):
        self.conversation_states = {
            "welcome": self.handle_welcome,
            "show_products": self.handle_show_products,
            "product_details": self.handle_product_details,
            "confirm_purchase": self.handle_confirm_purchase,
            "ai_tutor_prompt": self.handle_ai_tutor_prompt,
            "ai_question": self.handle_ai_question,
            "ai_quiz": self.handle_ai_quiz,
            "waiting_payment": self.handle_waiting_payment
        }
    
    def process_message(self, db: Session, phone_number: str, message: str) -> Dict[str, Any]:
        """Process incoming WhatsApp message"""
        try:
            # Get or create user
            user = self.get_or_create_user(db, phone_number)
            
            # Get active chat session
            session = self.get_or_create_session(db, user.id)
            
            # Parse message and determine next action
            current_step = session.current_step or "welcome"
            
            if current_step in self.conversation_states:
                response = self.conversation_states[current_step](db, user, session, message)
            else:
                response = self.handle_welcome(db, user, session, message)
            
            # Update session
            session.current_step = response.get("next_step", current_step)
            session.session_data = response.get("session_data", session.session_data)
            session.updated_at = datetime.utcnow()
            db.commit()
            
            return response
        except Exception as e:
            return {
                "success": False,
                "message": "I'm sorry, I encountered an error. Please try again.",
                "next_step": "welcome"
            }
    
    def get_or_create_user(self, db: Session, phone_number: str) -> User:
        """Get or create user by phone number"""
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            user = User(phone_number=phone_number, name="User")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    def get_or_create_session(self, db: Session, user_id: int) -> ChatSession:
        """Get or create active chat session"""
        session = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        ).first()
        
        if not session:
            session = ChatSession(
                user_id=user_id,
                session_data={},
                current_step="welcome"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        
        return session
    
    def handle_welcome(self, db: Session, user: User, sessio    n: ChatSession, message: str) -> Dict[str, Any]:
        """Handle welcome message and show main menu"""
        welcome_text = f"Hello {user.name or 'there'}! 👋\\n\\nWelcome to Isabi Store! I'm here to help you find and purchase amazing products.\\n\\nWhat would you like to do today?"
        
        buttons = [
            {"type": "reply", "reply": {"id": "browse_products", "title": "🛍️ Browse Products"}},
            {"type": "reply", "reply": {"id": "ai_tutor", "title": "🤖 AI Tutor"}},
            {"type": "reply", "reply": {"id": "my_orders", "title": "📦 My Orders"}}
        ]
        
        whatsapp_service.send_interactive_message(
            to=user.phone_number,
            header_text="Welcome to Isabi Store!",
            body_text=welcome_text,
            buttons=buttons
        )
        
        return {
            "success": True,
            "next_step": "main_menu",
            "session_data": session.session_data
        }
    
    def handle_show_products(self, db: Session, user: User, session: ChatSession, message: str) -> Dict[str, Any]:
        """Show available products"""
        products = db.query(Product).filter(Product.is_active == True).limit(10).all()
        
        if not products:
            whatsapp_service.send_message(
                to=user.phone_number,
                message="Sorry, no products are available at the moment."
            )
            return {"success": True, "next_step": "welcome"}
        
        # Create product list
        sections = []
        for product in products:
            sections.append({
                "title": product.name,
                "rows": [{
                    "id": f"product_{product.id}",
                    "title": product.name,
                    "description": f"${product.price:.2f} - {product.description[:50]}..."
                }]
            })
        
        whatsapp_service.send_list_message(
            to=user.phone_number,
            header_text="Our Products",
            body_text="Choose a product to view details:",
            button_text="View Products",
            sections=sections
        )
        
        return {
            "success": True,
            "next_step": "product_selection",
            "session_data": session.session_data
        }
    
    def handle_product_details(self, db: Session, user: User, session: ChatSession, message: str) -> Dict[str, Any]:
        """Show product details and purchase options"""
        # Extract product ID from message
        if "product_" in message:
            product_id = int(message.split("product_")[1])
        else:
            return {"success": False, "next_step": "show_products"}
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            whatsapp_service.send_message(
                to=user.phone_number,
                message="Product not found. Please try again."
            )
            return {"success": True, "next_step": "show_products"}
        
        # Store selected product in session
        session_data = session.session_data or {}
        session_data["selected_product_id"] = product_id
        
        product_text = f"*{product.name}*\\n\\n{product.description}\\n\\n💰 Price: ${product.price:.2f}\\n\\nWould you like to purchase this product?"
        
        buttons = [
            {"type": "reply", "reply": {"id": "buy_now", "title": "💳 Buy Now"}},
            {"type": "reply", "reply": {"id": "ask_question", "title": "❓ Ask Question"}},
            {"type": "reply", "reply": {"id": "back_to_products", "title": "⬅️ Back to Products"}}
        ]
        
        whatsapp_service.send_interactive_message(
            to=user.phone_number,
            header_text="Product Details",
            body_text=product_text,
            buttons=buttons
        )
        
        return {
            "success": True,
            "next_step": "product_details",
            "session_data": session_data
        }
    
    def handle_confirm_purchase(self, db: Session, user: User, session: ChatSession, message: str) -> Dict[str, Any]:
        """Handle purchase confirmation and create payment link"""
        session_data = session.session_data or {}
        product_id = session_data.get("selected_product_id")
        
        if not product_id:
            return {"success": False, "next_step": "show_products"}
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "next_step": "show_products"}
        
        # Create order
        order = Order(
            user_id=user.id,
            product_id=product.id,
            amount=product.price,
            status=OrderStatus.PENDING
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Create payment link
        payment_result = payment_service.create_payment_link(
            amount=product.price,
            product_name=product.name,
            order_id=order.id
        )
        
        if payment_result["success"]:
            # Update order with payment link
            order.payment_link = payment_result["payment_link"]
            order.payment_link_expires_at = payment_result["expires_at"]
            db.commit()
            
            payment_text = f"*Payment Link Generated*\\n\\nProduct: {product.name}\\nAmount: ${product.price:.2f}\\n\\n🔗 Payment Link:\\n{payment_result['payment_link']}\\n\\n⏰ This link expires in 5 minutes.\\n\\nPlease complete your payment to confirm your order."
            
            whatsapp_service.send_message(
                to=user.phone_number,
                message=payment_text
            )
            
            return {
                "success": True,
                "next_step": "waiting_payment",
                "session_data": {**session_data, "order_id": order.id}
            }
        else:
            whatsapp_service.send_message(
                to=user.phone_number,
                message="Sorry, I couldn't generate the payment link. Please try again later."
            )
            return {"success": True, "next_step": "show_products"}
    
    def handle_ai_tutor_prompt(self, db: Session, user: User, session: ChatSession, message: str) -> Dict[str, Any]:
        """Handle AI tutor access prompt"""
        if not user.ai_tutor_subscription or (user.ai_tutor_expires_at and user.ai_tutor_expires_at < datetime.utcnow()):
            # User needs to purchase AI tutor
            ai_tutor_text = "🤖 *AI Tutor Access Required*\\n\\nTo ask questions about products and get quizzes, you need to purchase our AI Tutor subscription.\\n\\nThe AI Tutor includes:\\n• Ask unlimited questions about any product\\n• Get personalized quizzes\\n• 24/7 AI assistance\\n\\nWould you like to purchase the AI Tutor for $9.99/month?"
            
            buttons = [
                {"type": "reply", "reply": {"id": "buy_ai_tutor", "title": "💳 Buy AI Tutor"}},
                {"type": "reply", "reply": {"id": "back_to_menu", "title": "⬅️ Back to Menu"}}
            ]
            
            whatsapp_service.send_interactive_message(
                to=user.phone_number,
                header_text="AI Tutor Subscription",
                body_text=ai_tutor_text,
                buttons=buttons
            )
            
            return {
                "success": True,
                "next_step": "ai_tutor_purchase",
                "session_data": session.session_data
            }
        else:
            # User has AI tutor access
            ai_text = "🤖 *AI Tutor Active*\\n\\nYou have access to our AI Tutor! What would you like to do?\\n\\n• Ask questions about any product\\n• Get personalized quizzes\\n• Get product recommendations"
            
            buttons = [
                {"type": "reply", "reply": {"id": "ask_question", "title": "❓ Ask Question"}},
                {"type": "reply", "reply": {"id": "take_quiz", "title": "🧠 Take Quiz"}},
                {"type": "reply", "reply": {"id": "back_to_menu", "title": "⬅️ Back to Menu"}}
            ]
            
            whatsapp_service.send_interactive_message(
                to=user.phone_number,
                header_text="AI Tutor",
                body_text=ai_text,
                buttons=buttons
            )
            
            return {
                "success": True,
                "next_step": "ai_tutor_menu",
                "session_data": session.session_data
            }
    
    def handle_ai_question(self, db: Session, user: User, session: ChatSession, message: str) -> Dict[str, Any]:
        """Handle AI question processing"""
        if not user.ai_tutor_subscription:
            return self.handle_ai_tutor_prompt(db, user, session, message)
        
        # Get product context if available
        session_data = session.session_data or {}
        product_id = session_data.get("selected_product_id")
        
        context_documents = []
        if product_id:
            context_documents = ai_service.search_product_knowledge(product_id, message)
        
        # Generate AI answer
        answer = ai_service.generate_answer(message, product_id, context_documents)
        
        whatsapp_service.send_message(
            to=user.phone_number,
            message=f"🤖 *AI Tutor Response*\\n\\n{answer}\\n\\nIs there anything else you'd like to know?"
        )
        
        return {
            "success": True,
            "next_step": "ai_tutor_menu",
            "session_data": session_data
        }
    
    def handle_ai_quiz(self, db: Session, user: User, session: ChatSession, message: str) -> Dict[str, Any]:
        """Handle AI quiz generation"""
        if not user.ai_tutor_subscription:
            return self.handle_ai_tutor_prompt(db, user, session, message)
        
        session_data = session.session_data or {}
        product_id = session_data.get("selected_product_id")
        
        # Generate quiz
        quiz = ai_service.generate_quiz(product_id)
        
        quiz_text = f"🧠 *Quiz Time!*\\n\\n{quiz['question']}\\n\\n"
        for i, option in enumerate(quiz['options']):
            quiz_text += f"{chr(65+i)}. {option}\\n"
        
        quiz_text += "\\nReply with the letter of your answer (A, B, C, or D)"
        
        whatsapp_service.send_message(
            to=user.phone_number,
            message=quiz_text
        )
        
        # Store quiz data for answer checking
        session_data["current_quiz"] = quiz
        return {
            "success": True,
            "next_step": "quiz_answer",
            "session_data": session_data
        }
    
    def handle_waiting_payment(self, db: Session, user: User, session: ChatSession, message: str) -> Dict[str, Any]:
        """Handle payment confirmation"""
        session_data = session.session_data or {}
        order_id = session_data.get("order_id")
        
        if order_id:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order and order.status == OrderStatus.PAID:
                whatsapp_service.send_message(
                    to=user.phone_number,
                    message="✅ *Payment Confirmed!*\\n\\nYour order has been successfully processed. Thank you for your purchase!"
                )
                return {"success": True, "next_step": "welcome"}
        
        whatsapp_service.send_message(
            to=user.phone_number,
            message="Please complete your payment using the provided link, or type 'cancel' to cancel the order."
        )
        
        return {
            "success": True,
            "next_step": "waiting_payment",
            "session_data": session_data
        }

# Global instance
chatbot_service = ChatbotService()
