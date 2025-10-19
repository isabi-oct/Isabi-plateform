"""
Database Tools for Agentic AI System

This module provides tools for database operations using SQLAlchemy ORM.
These tools allow the agent to access and modify data autonomously.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from Backend.models.database.database import get_db
from Backend.models.database.models import User, Product, Order, ChatSession, AIQuestion, Quiz, OrderStatus, ProductType, UserStatus

logger = logging.getLogger(__name__)

# Pydantic models for tool inputs
class UserSearchInput(BaseModel):
    phone_number: Optional[str] = Field(None, description="Phone number to search for")
    user_id: Optional[int] = Field(None, description="User ID to search for")
    name: Optional[str] = Field(None, description="Name to search for")

class ProductSearchInput(BaseModel):
    product_id: Optional[int] = Field(None, description="Product ID to search for")
    name: Optional[str] = Field(None, description="Product name to search for")
    product_type: Optional[str] = Field(None, description="Product type (regular or ai_tutor)")
    min_price: Optional[float] = Field(None, description="Minimum price")
    max_price: Optional[float] = Field(None, description="Maximum price")
    is_active: Optional[bool] = Field(True, description="Whether product is active")

class OrderSearchInput(BaseModel):
    order_id: Optional[int] = Field(None, description="Order ID to search for")
    user_id: Optional[int] = Field(None, description="User ID to search for")
    status: Optional[str] = Field(None, description="Order status")
    product_id: Optional[int] = Field(None, description="Product ID to search for")

class CreateUserInput(BaseModel):
    phone_number: str = Field(..., description="User's phone number")
    name: Optional[str] = Field(None, description="User's name")
    status: str = Field("active", description="User status")

class CreateOrderInput(BaseModel):
    user_id: int = Field(..., description="User ID")
    product_id: int = Field(..., description="Product ID")
    amount: float = Field(..., description="Order amount")

class UpdateOrderStatusInput(BaseModel):
    order_id: int = Field(..., description="Order ID to update")
    status: str = Field(..., description="New status")

class DatabaseTools:
    """Database tools for agentic AI system."""
    
    # Constants
    USER_NOT_FOUND = "User not found"
    PRODUCT_NOT_FOUND = "Product not found"
    ORDER_NOT_FOUND = "Order not found"
    
    def __init__(self):
        self.db_session = None
        logger.info("Database tools initialized")
    
    def _get_db_session(self) -> Session:
        """Get database session."""
        if self.db_session is None:
            self.db_session = next(get_db())
        return self.db_session
    
    def get_tools(self) -> List[BaseTool]:
        """Get all database tools."""
        return [
            self.search_users,
            self.get_user_by_id,
            self.create_user,
            self.update_user,
            self.search_products,
            self.get_product_by_id,
            self.search_orders,
            self.get_order_by_id,
            self.create_order,
            self.update_order_status,
            self.get_user_orders,
            self.get_product_orders,
            self.get_chat_session,
            self.create_chat_session,
            self.update_chat_session,
            self.get_ai_questions,
            self.get_quizzes
        ]
    
    @tool("search_users", args_schema=UserSearchInput)
    def search_users(self, phone_number: Optional[str] = None, user_id: Optional[int] = None, 
                    name: Optional[str] = None) -> Dict[str, Any]:
        """Search for users based on phone number, user ID, or name."""
        try:
            db = self._get_db_session()
            query = db.query(User)
            
            if phone_number:
                query = query.filter(User.phone_number == phone_number)
            if user_id:
                query = query.filter(User.id == user_id)
            if name:
                query = query.filter(User.name.ilike(f"%{name}%"))
            
            users = query.all()
            
            result = {
                "success": True,
                "count": len(users),
                "users": [
                    {
                        "id": user.id,
                        "phone_number": user.phone_number,
                        "name": user.name,
                        "status": user.status,
                        "ai_tutor_subscription": user.ai_tutor_subscription,
                        "created_at": user.created_at.isoformat() if user.created_at else None
                    }
                    for user in users
                ]
            }
            
            logger.info(f"Found {len(users)} users")
            return result
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_user_by_id", args_schema=dict)
    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID."""
        try:
            db = self._get_db_session()
            user = db.query(User).filter(User.id == user_id).first()
            
            if user:
                return {
                    "success": True,
                    "user": {
                        "id": user.id,
                        "phone_number": user.phone_number,
                        "name": user.name,
                        "status": user.status,
                        "ai_tutor_subscription": user.ai_tutor_subscription,
                        "ai_tutor_expires_at": user.ai_tutor_expires_at.isoformat() if user.ai_tutor_expires_at else None,
                        "created_at": user.created_at.isoformat() if user.created_at else None
                    }
                }
            else:
                return {"success": False, "error": self.USER_NOT_FOUND}
                
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("create_user", args_schema=CreateUserInput)
    def create_user(self, phone_number: str, name: Optional[str] = None, status: str = "active") -> Dict[str, Any]:
        """Create a new user."""
        try:
            db = self._get_db_session()
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.phone_number == phone_number).first()
            if existing_user:
                return {
                    "success": False,
                    "error": "User with this phone number already exists",
                    "user_id": existing_user.id
                }
            
            # Create new user
            user = User(
                phone_number=phone_number,
                name=name or f"User_{phone_number[-4:]}",
                status=status
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created user with ID {user.id}")
            return {
                "success": True,
                "user_id": user.id,
                "message": "User created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("update_user", args_schema=dict)
    def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Update user information."""
        try:
            db = self._get_db_session()
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {"success": False, "error": self.USER_NOT_FOUND}
            
            # Update allowed fields
            allowed_fields = ['name', 'status', 'ai_tutor_subscription', 'ai_tutor_expires_at']
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"Updated user {user_id}")
            return {"success": True, "message": "User updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("search_products", args_schema=ProductSearchInput)
    def search_products(self, product_id: Optional[int] = None, name: Optional[str] = None,
                       product_type: Optional[str] = None, min_price: Optional[float] = None,
                       max_price: Optional[float] = None, is_active: bool = True) -> Dict[str, Any]:
        """Search for products based on various criteria."""
        try:
            db = self._get_db_session()
            query = db.query(Product)
            
            if product_id:
                query = query.filter(Product.id == product_id)
            if name:
                query = query.filter(Product.name.ilike(f"%{name}%"))
            if product_type:
                query = query.filter(Product.product_type == product_type)
            if min_price is not None:
                query = query.filter(Product.price >= min_price)
            if max_price is not None:
                query = query.filter(Product.price <= max_price)
            if is_active is not None:
                query = query.filter(Product.is_active == is_active)
            
            products = query.all()
            
            result = {
                "success": True,
                "count": len(products),
                "products": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "price": product.price,
                        "product_type": product.product_type,
                        "is_active": product.is_active,
                        "vector_collection_id": product.vector_collection_id,
                        "created_at": product.created_at.isoformat() if product.created_at else None
                    }
                    for product in products
                ]
            }
            
            logger.info(f"Found {len(products)} products")
            return result
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_product_by_id", args_schema=dict)
    def get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """Get product by ID."""
        try:
            db = self._get_db_session()
            product = db.query(Product).filter(Product.id == product_id).first()
            
            if product:
                return {
                    "success": True,
                    "product": {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "price": product.price,
                        "product_type": product.product_type,
                        "is_active": product.is_active,
                        "vector_collection_id": product.vector_collection_id,
                        "created_at": product.created_at.isoformat() if product.created_at else None
                    }
                }
            else:
                return {"success": False, "error": self.PRODUCT_NOT_FOUND}
                
        except Exception as e:
            logger.error(f"Error getting product by ID: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("search_orders", args_schema=OrderSearchInput)
    def search_orders(self, order_id: Optional[int] = None, user_id: Optional[int] = None,
                     status: Optional[str] = None, product_id: Optional[int] = None) -> Dict[str, Any]:
        """Search for orders based on various criteria."""
        try:
            db = self._get_db_session()
            query = db.query(Order)
            
            if order_id:
                query = query.filter(Order.id == order_id)
            if user_id:
                query = query.filter(Order.user_id == user_id)
            if status:
                query = query.filter(Order.status == status)
            if product_id:
                query = query.filter(Order.product_id == product_id)
            
            orders = query.order_by(desc(Order.created_at)).all()
            
            result = {
                "success": True,
                "count": len(orders),
                "orders": [
                    {
                        "id": order.id,
                        "user_id": order.user_id,
                        "product_id": order.product_id,
                        "amount": order.amount,
                        "status": order.status,
                        "payment_link": order.payment_link,
                        "payment_link_expires_at": order.payment_link_expires_at.isoformat() if order.payment_link_expires_at else None,
                        "flutterwave_payment_id": order.flutterwave_payment_id,
                        "flutterwave_transaction_id": order.flutterwave_transaction_id,
                        "created_at": order.created_at.isoformat() if order.created_at else None
                    }
                    for order in orders
                ]
            }
            
            logger.info(f"Found {len(orders)} orders")
            return result
            
        except Exception as e:
            logger.error(f"Error searching orders: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_order_by_id", args_schema=dict)
    def get_order_by_id(self, order_id: int) -> Dict[str, Any]:
        """Get order by ID."""
        try:
            db = self._get_db_session()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if order:
                return {
                    "success": True,
                    "order": {
                        "id": order.id,
                        "user_id": order.user_id,
                        "product_id": order.product_id,
                        "amount": order.amount,
                        "status": order.status,
                        "payment_link": order.payment_link,
                        "payment_link_expires_at": order.payment_link_expires_at.isoformat() if order.payment_link_expires_at else None,
                        "flutterwave_payment_id": order.flutterwave_payment_id,
                        "flutterwave_transaction_id": order.flutterwave_transaction_id,
                        "created_at": order.created_at.isoformat() if order.created_at else None
                    }
                }
            else:
                return {"success": False, "error": self.ORDER_NOT_FOUND}
                
        except Exception as e:
            logger.error(f"Error getting order by ID: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("create_order", args_schema=CreateOrderInput)
    def create_order(self, user_id: int, product_id: int, amount: float) -> Dict[str, Any]:
        """Create a new order."""
        try:
            db = self._get_db_session()
            
            # Verify user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": self.USER_NOT_FOUND}
            
            # Verify product exists
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"success": False, "error": "Product not found"}
            
            # Create new order
            order = Order(
                user_id=user_id,
                product_id=product_id,
                amount=amount,
                status=OrderStatus.PENDING
            )
            
            db.add(order)
            db.commit()
            db.refresh(order)
            
            logger.info(f"Created order with ID {order.id}")
            return {
                "success": True,
                "order_id": order.id,
                "message": "Order created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("update_order_status", args_schema=UpdateOrderStatusInput)
    def update_order_status(self, order_id: int, status: str) -> Dict[str, Any]:
        """Update order status."""
        try:
            db = self._get_db_session()
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Validate status
            valid_statuses = [s.value for s in OrderStatus]
            if status not in valid_statuses:
                return {"success": False, "error": f"Invalid status. Valid statuses: {valid_statuses}"}
            
            order.status = status
            order.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"Updated order {order_id} status to {status}")
            return {"success": True, "message": "Order status updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("get_user_orders", args_schema=dict)
    def get_user_orders(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get orders for a specific user."""
        try:
            db = self._get_db_session()
            orders = db.query(Order).filter(Order.user_id == user_id).order_by(desc(Order.created_at)).limit(limit).all()
            
            result = {
                "success": True,
                "count": len(orders),
                "orders": [
                    {
                        "id": order.id,
                        "product_id": order.product_id,
                        "amount": order.amount,
                        "status": order.status,
                        "created_at": order.created_at.isoformat() if order.created_at else None
                    }
                    for order in orders
                ]
            }
            
            logger.info(f"Found {len(orders)} orders for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_product_orders", args_schema=dict)
    def get_product_orders(self, product_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get orders for a specific product."""
        try:
            db = self._get_db_session()
            orders = db.query(Order).filter(Order.product_id == product_id).order_by(desc(Order.created_at)).limit(limit).all()
            
            result = {
                "success": True,
                "count": len(orders),
                "orders": [
                    {
                        "id": order.id,
                        "user_id": order.user_id,
                        "amount": order.amount,
                        "status": order.status,
                        "created_at": order.created_at.isoformat() if order.created_at else None
                    }
                    for order in orders
                ]
            }
            
            logger.info(f"Found {len(orders)} orders for product {product_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting product orders: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_chat_session", args_schema=dict)
    def get_chat_session(self, user_id: int) -> Dict[str, Any]:
        """Get active chat session for a user."""
        try:
            db = self._get_db_session()
            session = db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).first()
            
            if session:
                return {
                    "success": True,
                    "session": {
                        "id": session.id,
                        "user_id": session.user_id,
                        "session_data": session.session_data,
                        "current_step": session.current_step,
                        "is_active": session.is_active,
                        "created_at": session.created_at.isoformat() if session.created_at else None
                    }
                }
            else:
                return {"success": False, "error": "No active chat session found"}
                
        except Exception as e:
            logger.error(f"Error getting chat session: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("create_chat_session", args_schema=dict)
    def create_chat_session(self, user_id: int, session_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new chat session."""
        try:
            db = self._get_db_session()
            
            # Deactivate existing sessions
            db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).update({"is_active": False})
            
            # Create new session
            session = ChatSession(
                user_id=user_id,
                session_data=session_data or {},
                current_step="greeting",
                is_active=True
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"Created chat session {session.id} for user {user_id}")
            return {
                "success": True,
                "session_id": session.id,
                "message": "Chat session created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("update_chat_session", args_schema=dict)
    def update_chat_session(self, session_id: int, session_data: Optional[Dict[str, Any]] = None,
                           current_step: Optional[str] = None) -> Dict[str, Any]:
        """Update chat session."""
        try:
            db = self._get_db_session()
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            
            if not session:
                return {"success": False, "error": "Chat session not found"}
            
            if session_data is not None:
                session.session_data = session_data
            if current_step is not None:
                session.current_step = current_step
            
            session.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"Updated chat session {session_id}")
            return {"success": True, "message": "Chat session updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating chat session: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("get_ai_questions", args_schema=dict)
    def get_ai_questions(self, product_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get AI questions for a product."""
        try:
            db = self._get_db_session()
            questions = db.query(AIQuestion).filter(
                AIQuestion.product_id == product_id
            ).limit(limit).all()
            
            result = {
                "success": True,
                "count": len(questions),
                "questions": [
                    {
                        "id": question.id,
                        "product_id": question.product_id,
                        "question": question.question,
                        "answer": question.answer,
                        "vector_id": question.vector_id,
                        "created_at": question.created_at.isoformat() if question.created_at else None
                    }
                    for question in questions
                ]
            }
            
            logger.info(f"Found {len(questions)} AI questions for product {product_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting AI questions: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_quizzes", args_schema=dict)
    def get_quizzes(self, product_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get quizzes for a product."""
        try:
            db = self._get_db_session()
            quizzes = db.query(Quiz).filter(
                Quiz.product_id == product_id
            ).limit(limit).all()
            
            result = {
                "success": True,
                "count": len(quizzes),
                "quizzes": [
                    {
                        "id": quiz.id,
                        "product_id": quiz.product_id,
                        "question": quiz.question,
                        "options": quiz.options,
                        "correct_answer": quiz.correct_answer,
                        "explanation": quiz.explanation,
                        "created_at": quiz.created_at.isoformat() if quiz.created_at else None
                    }
                    for quiz in quizzes
                ]
            }
            
            logger.info(f"Found {len(quizzes)} quizzes for product {product_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting quizzes: {e}")
            return {"success": False, "error": str(e)}
