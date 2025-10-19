"""
Product Tools for Agentic AI System

This module provides tools for managing products, especially AI-trainable products
with tutoring capabilities and personalized learning experiences.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from Backend.models.database.database import get_db
from Backend.models.database.models import Product, User, Order, AIQuestion, Quiz, ProductType, OrderStatus

logger = logging.getLogger(__name__)

# Pydantic models for tool inputs
class CreateProductInput(BaseModel):
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    product_type: str = Field("regular", description="Product type (regular or ai_tutor)")
    vector_collection_id: Optional[str] = Field(None, description="Vector collection ID for AI products")

class UpdateProductInput(BaseModel):
    product_id: int = Field(..., description="Product ID to update")
    name: Optional[str] = Field(None, description="New product name")
    description: Optional[str] = Field(None, description="New product description")
    price: Optional[float] = Field(None, description="New product price")
    is_active: Optional[bool] = Field(None, description="Whether product is active")

class CreateAIQuestionInput(BaseModel):
    product_id: int = Field(..., description="Product ID")
    question: str = Field(..., description="Question text")
    answer: str = Field(..., description="Answer text")
    vector_id: Optional[str] = Field(None, description="Vector ID for semantic search")

class CreateQuizInput(BaseModel):
    product_id: int = Field(..., description="Product ID")
    question: str = Field(..., description="Quiz question")
    options: List[str] = Field(..., description="Answer options")
    correct_answer: int = Field(..., description="Index of correct answer (0-based)")
    explanation: Optional[str] = Field(None, description="Explanation for the answer")

class StartTutoringSessionInput(BaseModel):
    user_id: int = Field(..., description="User ID")
    product_id: int = Field(..., description="Product ID for tutoring")
    session_type: str = Field("q_and_a", description="Type of tutoring session")

class ProductTools:
    """Product tools for agentic AI system."""
    
    def __init__(self):
        logger.info("Product tools initialized")
    
    def get_tools(self) -> List[BaseTool]:
        """Get all product tools."""
        return [
            self.create_product,
            self.update_product,
            self.get_product_details,
            self.search_products_by_type,
            self.get_ai_tutor_products,
            self.create_ai_question,
            self.create_quiz,
            self.get_product_questions,
            self.get_product_quizzes,
            self.start_tutoring_session,
            self.check_user_tutoring_access,
            self.get_product_recommendations,
            self.get_product_analytics
        ]
    
    @tool("create_product", args_schema=CreateProductInput)
    def create_product(self, name: str, description: str, price: float, 
                      product_type: str = "regular", vector_collection_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new product."""
        try:
            db = next(get_db())
            
            # Validate product type
            valid_types = [t.value for t in ProductType]
            if product_type not in valid_types:
                return {"success": False, "error": f"Invalid product type. Valid types: {valid_types}"}
            
            # Create new product
            product = Product(
                name=name,
                description=description,
                price=price,
                product_type=product_type,
                vector_collection_id=vector_collection_id,
                is_active=True
            )
            
            db.add(product)
            db.commit()
            db.refresh(product)
            
            logger.info(f"Created product with ID {product.id}")
            return {
                "success": True,
                "product_id": product.id,
                "message": "Product created successfully",
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "product_type": product.product_type,
                    "is_active": product.is_active,
                    "vector_collection_id": product.vector_collection_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("update_product", args_schema=UpdateProductInput)
    def update_product(self, product_id: int, name: Optional[str] = None, 
                      description: Optional[str] = None, price: Optional[float] = None,
                      is_active: Optional[bool] = None) -> Dict[str, Any]:
        """Update product information."""
        try:
            db = next(get_db())
            product = db.query(Product).filter(Product.id == product_id).first()
            
            if not product:
                return {"success": False, "error": "Product not found"}
            
            # Update fields
            if name is not None:
                product.name = name
            if description is not None:
                product.description = description
            if price is not None:
                product.price = price
            if is_active is not None:
                product.is_active = is_active
            
            product.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"Updated product {product_id}")
            return {
                "success": True,
                "message": "Product updated successfully",
                "product_id": product_id
            }
            
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("get_product_details", args_schema=dict)
    def get_product_details(self, product_id: int) -> Dict[str, Any]:
        """Get detailed product information including AI features."""
        try:
            db = next(get_db())
            product = db.query(Product).filter(Product.id == product_id).first()
            
            if not product:
                return {"success": False, "error": "Product not found"}
            
            # Get AI questions count
            ai_questions_count = db.query(AIQuestion).filter(AIQuestion.product_id == product_id).count()
            
            # Get quizzes count
            quizzes_count = db.query(Quiz).filter(Quiz.product_id == product_id).count()
            
            # Get order statistics
            orders_count = db.query(Order).filter(Order.product_id == product_id).count()
            paid_orders_count = db.query(Order).filter(
                Order.product_id == product_id,
                Order.status == OrderStatus.PAID
            ).count()
            
            product_details = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "product_type": product.product_type,
                "is_active": product.is_active,
                "vector_collection_id": product.vector_collection_id,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None,
                "ai_features": {
                    "has_vector_collection": product.vector_collection_id is not None,
                    "ai_questions_count": ai_questions_count,
                    "quizzes_count": quizzes_count,
                    "is_ai_tutor": product.product_type == ProductType.AI_TUTOR
                },
                "sales_stats": {
                    "total_orders": orders_count,
                    "paid_orders": paid_orders_count,
                    "conversion_rate": (paid_orders_count / orders_count * 100) if orders_count > 0 else 0
                }
            }
            
            return {
                "success": True,
                "product": product_details
            }
            
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("search_products_by_type", args_schema=dict)
    def search_products_by_type(self, product_type: str, limit: int = 10) -> Dict[str, Any]:
        """Search products by type."""
        try:
            db = next(get_db())
            products = db.query(Product).filter(
                Product.product_type == product_type,
                Product.is_active == True
            ).limit(limit).all()
            
            result = {
                "success": True,
                "product_type": product_type,
                "count": len(products),
                "products": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "price": product.price,
                        "product_type": product.product_type,
                        "vector_collection_id": product.vector_collection_id
                    }
                    for product in products
                ]
            }
            
            logger.info(f"Found {len(products)} products of type {product_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error searching products by type: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_ai_tutor_products", args_schema=dict)
    def get_ai_tutor_products(self, limit: int = 10) -> Dict[str, Any]:
        """Get all AI tutor products with tutoring capabilities."""
        try:
            db = next(get_db())
            products = db.query(Product).filter(
                Product.product_type == ProductType.AI_TUTOR,
                Product.is_active == True
            ).limit(limit).all()
            
            # Enhance with AI features
            enhanced_products = []
            for product in products:
                # Get AI questions count
                ai_questions_count = db.query(AIQuestion).filter(AIQuestion.product_id == product.id).count()
                
                # Get quizzes count
                quizzes_count = db.query(Quiz).filter(Quiz.product_id == product.id).count()
                
                enhanced_products.append({
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "vector_collection_id": product.vector_collection_id,
                    "ai_features": {
                        "has_vector_collection": product.vector_collection_id is not None,
                        "ai_questions_count": ai_questions_count,
                        "quizzes_count": quizzes_count,
                        "tutoring_available": True
                    }
                })
            
            return {
                "success": True,
                "count": len(enhanced_products),
                "products": enhanced_products
            }
            
        except Exception as e:
            logger.error(f"Error getting AI tutor products: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("create_ai_question", args_schema=CreateAIQuestionInput)
    def create_ai_question(self, product_id: int, question: str, answer: str, 
                          vector_id: Optional[str] = None) -> Dict[str, Any]:
        """Create an AI question for a product."""
        try:
            db = next(get_db())
            
            # Verify product exists and is AI tutor type
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"success": False, "error": "Product not found"}
            
            if product.product_type != ProductType.AI_TUTOR:
                return {"success": False, "error": "Product is not an AI tutor product"}
            
            # Create AI question
            ai_question = AIQuestion(
                product_id=product_id,
                question=question,
                answer=answer,
                vector_id=vector_id
            )
            
            db.add(ai_question)
            db.commit()
            db.refresh(ai_question)
            
            logger.info(f"Created AI question {ai_question.id} for product {product_id}")
            return {
                "success": True,
                "question_id": ai_question.id,
                "message": "AI question created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating AI question: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("create_quiz", args_schema=CreateQuizInput)
    def create_quiz(self, product_id: int, question: str, options: List[str], 
                   correct_answer: int, explanation: Optional[str] = None) -> Dict[str, Any]:
        """Create a quiz for a product."""
        try:
            db = next(get_db())
            
            # Verify product exists
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"success": False, "error": "Product not found"}
            
            # Validate correct answer index
            if correct_answer < 0 or correct_answer >= len(options):
                return {"success": False, "error": "Invalid correct answer index"}
            
            # Create quiz
            quiz = Quiz(
                product_id=product_id,
                question=question,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation
            )
            
            db.add(quiz)
            db.commit()
            db.refresh(quiz)
            
            logger.info(f"Created quiz {quiz.id} for product {product_id}")
            return {
                "success": True,
                "quiz_id": quiz.id,
                "message": "Quiz created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating quiz: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @tool("get_product_questions", args_schema=dict)
    def get_product_questions(self, product_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get AI questions for a product."""
        try:
            db = next(get_db())
            questions = db.query(AIQuestion).filter(
                AIQuestion.product_id == product_id
            ).limit(limit).all()
            
            return {
                "success": True,
                "product_id": product_id,
                "count": len(questions),
                "questions": [
                    {
                        "id": question.id,
                        "question": question.question,
                        "answer": question.answer,
                        "vector_id": question.vector_id,
                        "created_at": question.created_at.isoformat() if question.created_at else None
                    }
                    for question in questions
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting product questions: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_product_quizzes", args_schema=dict)
    def get_product_quizzes(self, product_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get quizzes for a product."""
        try:
            db = next(get_db())
            quizzes = db.query(Quiz).filter(
                Quiz.product_id == product_id
            ).limit(limit).all()
            
            return {
                "success": True,
                "product_id": product_id,
                "count": len(quizzes),
                "quizzes": [
                    {
                        "id": quiz.id,
                        "question": quiz.question,
                        "options": quiz.options,
                        "correct_answer": quiz.correct_answer,
                        "explanation": quiz.explanation,
                        "created_at": quiz.created_at.isoformat() if quiz.created_at else None
                    }
                    for quiz in quizzes
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting product quizzes: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("start_tutoring_session", args_schema=StartTutoringSessionInput)
    def start_tutoring_session(self, user_id: int, product_id: int, 
                              session_type: str = "q_and_a") -> Dict[str, Any]:
        """Start a tutoring session for a user with an AI tutor product."""
        try:
            db = next(get_db())
            
            # Verify user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Verify product exists and is AI tutor type
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"success": False, "error": "Product not found"}
            
            if product.product_type != ProductType.AI_TUTOR:
                return {"success": False, "error": "Product is not an AI tutor product"}
            
            # Check if user has access to this product
            has_access = self._check_user_product_access(user_id, product_id)
            if not has_access:
                return {"success": False, "error": "User does not have access to this product"}
            
            # Create tutoring session
            session_data = {
                "session_type": session_type,
                "product_id": product_id,
                "started_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # Update user's chat session
            chat_session = db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).first()
            
            if chat_session:
                current_data = chat_session.session_data or {}
                current_data["tutoring_session"] = session_data
                chat_session.session_data = current_data
                chat_session.current_step = "tutoring"
                db.commit()
            
            logger.info(f"Started tutoring session for user {user_id} with product {product_id}")
            return {
                "success": True,
                "session_data": session_data,
                "message": "Tutoring session started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting tutoring session: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("check_user_tutoring_access", args_schema=dict)
    def check_user_tutoring_access(self, user_id: int, product_id: int) -> Dict[str, Any]:
        """Check if user has access to tutoring for a product."""
        try:
            has_access = self._check_user_product_access(user_id, product_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "product_id": product_id,
                "has_access": has_access
            }
            
        except Exception as e:
            logger.error(f"Error checking user tutoring access: {e}")
            return {"success": False, "error": str(e)}
    
    def _check_user_product_access(self, user_id: int, product_id: int) -> bool:
        """Check if user has access to a product (has paid for it)."""
        try:
            db = next(get_db())
            
            # Check if user has a paid order for this product
            paid_order = db.query(Order).filter(
                Order.user_id == user_id,
                Order.product_id == product_id,
                Order.status == OrderStatus.PAID
            ).first()
            
            return paid_order is not None
            
        except Exception as e:
            logger.error(f"Error checking user product access: {e}")
            return False
    
    @tool("get_product_recommendations", args_schema=dict)
    def get_product_recommendations(self, user_id: int, limit: int = 5) -> Dict[str, Any]:
        """Get personalized product recommendations for a user."""
        try:
            db = next(get_db())
            
            # Get user's purchase history
            user_orders = db.query(Order).filter(
                Order.user_id == user_id,
                Order.status == OrderStatus.PAID
            ).all()
            
            purchased_product_ids = [order.product_id for order in user_orders]
            
            # Get products user hasn't purchased
            available_products = db.query(Product).filter(
                Product.is_active == True,
                ~Product.id.in_(purchased_product_ids)
            ).limit(limit * 2).all()  # Get more than needed for filtering
            
            # Simple recommendation logic (can be enhanced with ML)
            recommendations = []
            for product in available_products:
                # Calculate recommendation score based on product type and price
                score = 0.5  # Base score
                
                # Boost AI tutor products
                if product.product_type == ProductType.AI_TUTOR:
                    score += 0.3
                
                # Boost based on popularity (orders count)
                orders_count = db.query(Order).filter(
                    Order.product_id == product.id,
                    Order.status == OrderStatus.PAID
                ).count()
                score += min(orders_count * 0.1, 0.2)  # Cap at 0.2
                
                recommendations.append({
                    "product": {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "price": product.price,
                        "product_type": product.product_type
                    },
                    "score": score,
                    "reason": "Based on your interests and popular products"
                })
            
            # Sort by score and limit results
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            recommendations = recommendations[:limit]
            
            return {
                "success": True,
                "user_id": user_id,
                "recommendations": recommendations,
                "count": len(recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error getting product recommendations: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_product_analytics", args_schema=dict)
    def get_product_analytics(self, product_id: int) -> Dict[str, Any]:
        """Get analytics for a product."""
        try:
            db = next(get_db())
            
            # Get product
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"success": False, "error": "Product not found"}
            
            # Get order statistics
            total_orders = db.query(Order).filter(Order.product_id == product_id).count()
            paid_orders = db.query(Order).filter(
                Order.product_id == product_id,
                Order.status == OrderStatus.PAID
            ).count()
            pending_orders = db.query(Order).filter(
                Order.product_id == product_id,
                Order.status == OrderStatus.PENDING
            ).count()
            
            # Get revenue
            paid_orders_query = db.query(Order).filter(
                Order.product_id == product_id,
                Order.status == OrderStatus.PAID
            )
            total_revenue = sum(order.amount for order in paid_orders_query.all())
            
            # Get AI features statistics
            ai_questions_count = db.query(AIQuestion).filter(AIQuestion.product_id == product_id).count()
            quizzes_count = db.query(Quiz).filter(Quiz.product_id == product_id).count()
            
            return {
                "success": True,
                "product_id": product_id,
                "analytics": {
                    "sales": {
                        "total_orders": total_orders,
                        "paid_orders": paid_orders,
                        "pending_orders": pending_orders,
                        "conversion_rate": (paid_orders / total_orders * 100) if total_orders > 0 else 0,
                        "total_revenue": total_revenue
                    },
                    "ai_features": {
                        "ai_questions_count": ai_questions_count,
                        "quizzes_count": quizzes_count,
                        "has_vector_collection": product.vector_collection_id is not None,
                        "is_ai_tutor": product.product_type == ProductType.AI_TUTOR
                    },
                    "product_info": {
                        "name": product.name,
                        "price": product.price,
                        "product_type": product.product_type,
                        "is_active": product.is_active
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting product analytics: {e}")
            return {"success": False, "error": str(e)}
