"""
Vector Search Tools for Agentic AI System

This module provides tools for vector search operations using GCP Vertex AI Vector Search.
These tools allow the agent to perform semantic search for AI-related Q&A and product knowledge.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from Backend.config.gcp_config import gcp_config
from Backend.models.database.database import get_db
from Backend.models.database.models import Product, AIQuestion

logger = logging.getLogger(__name__)

# Pydantic models for tool inputs
class VectorSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    product_id: Optional[int] = Field(None, description="Product ID to search within")
    limit: int = Field(5, description="Maximum number of results to return")
    threshold: float = Field(0.7, description="Similarity threshold (0-1)")

class AddToVectorIndexInput(BaseModel):
    content: str = Field(..., description="Content to add to vector index")
    product_id: int = Field(..., description="Product ID this content belongs to")
    content_type: str = Field("question", description="Type of content (question, answer, description)")

class VectorSearchTools:
    """Vector search tools for agentic AI system."""
    
    def __init__(self):
        self.gcp_config = gcp_config
        self.vector_client = None
        self._initialize_vector_client()
        logger.info("Vector search tools initialized")
    
    def _initialize_vector_client(self):
        """Initialize GCP Vector Search client."""
        try:
            from Database.VectorDB.gcp_vector_client import GCPVectorClient
            self.vector_client = GCPVectorClient()
            logger.info("GCP Vector Search client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector client: {e}")
            self.vector_client = None
    
    def get_tools(self) -> List[BaseTool]:
        """Get all vector search tools."""
        return [
            self.search_product_knowledge,
            self.search_ai_questions,
            self.search_similar_products,
            self.add_content_to_vector_index,
            self.get_vector_collection_info,
            self.semantic_product_search
        ]
    
    @tool("search_product_knowledge", args_schema=VectorSearchInput)
    def search_product_knowledge(self, query: str, product_id: Optional[int] = None, 
                               limit: int = 5, threshold: float = 0.7) -> Dict[str, Any]:
        """Search for product knowledge using vector similarity."""
        try:
            if not self.vector_client:
                return {"success": False, "error": "Vector search client not available"}
            
            # Get product information if product_id is provided
            product_info = None
            if product_id:
                db = next(get_db())
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    product_info = {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "product_type": product.product_type,
                        "vector_collection_id": product.vector_collection_id
                    }
            
            # Perform vector search
            search_results = self.vector_client.search(
                query=query,
                collection_id=product_info["vector_collection_id"] if product_info else None,
                limit=limit,
                threshold=threshold
            )
            
            if search_results["success"]:
                # Enhance results with product information
                enhanced_results = []
                for result in search_results["results"]:
                    enhanced_result = result.copy()
                    if product_info:
                        enhanced_result["product_info"] = product_info
                    enhanced_results.append(enhanced_result)
                
                return {
                    "success": True,
                    "query": query,
                    "results": enhanced_results,
                    "total_found": len(enhanced_results),
                    "product_id": product_id
                }
            else:
                return {"success": False, "error": search_results["error"]}
                
        except Exception as e:
            logger.error(f"Error searching product knowledge: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("search_ai_questions", args_schema=VectorSearchInput)
    def search_ai_questions(self, query: str, product_id: Optional[int] = None, 
                           limit: int = 5, threshold: float = 0.7) -> Dict[str, Any]:
        """Search for AI questions and answers using vector similarity."""
        try:
            if not self.vector_client:
                return {"success": False, "error": "Vector search client not available"}
            
            # Get AI questions from database
            db = next(get_db())
            questions_query = db.query(AIQuestion)
            
            if product_id:
                questions_query = questions_query.filter(AIQuestion.product_id == product_id)
            
            questions = questions_query.all()
            
            if not questions:
                return {
                    "success": True,
                    "query": query,
                    "results": [],
                    "total_found": 0,
                    "message": "No AI questions found for this product"
                }
            
            # Perform vector search on questions
            search_results = []
            for question in questions:
                if question.vector_id:
                    # Search using the stored vector ID
                    result = self.vector_client.search_by_id(
                        vector_id=question.vector_id,
                        query=query,
                        threshold=threshold
                    )
                    
                    if result["success"] and result["similarity"] >= threshold:
                        search_results.append({
                            "id": question.id,
                            "product_id": question.product_id,
                            "question": question.question,
                            "answer": question.answer,
                            "similarity": result["similarity"],
                            "vector_id": question.vector_id
                        })
            
            # Sort by similarity and limit results
            search_results.sort(key=lambda x: x["similarity"], reverse=True)
            search_results = search_results[:limit]
            
            return {
                "success": True,
                "query": query,
                "results": search_results,
                "total_found": len(search_results),
                "product_id": product_id
            }
            
        except Exception as e:
            logger.error(f"Error searching AI questions: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("search_similar_products", args_schema=VectorSearchInput)
    def search_similar_products(self, query: str, product_id: Optional[int] = None, 
                               limit: int = 5, threshold: float = 0.7) -> Dict[str, Any]:
        """Search for similar products using vector similarity."""
        try:
            if not self.vector_client:
                return {"success": False, "error": "Vector search client not available"}
            
            # Get all products with vector collections
            db = next(get_db())
            products = db.query(Product).filter(
                Product.is_active == True,
                Product.vector_collection_id.isnot(None)
            ).all()
            
            if not products:
                return {
                    "success": True,
                    "query": query,
                    "results": [],
                    "total_found": 0,
                    "message": "No products with vector collections found"
                }
            
            # Search across all product vector collections
            all_results = []
            for product in products:
                if product.vector_collection_id:
                    search_results = self.vector_client.search(
                        query=query,
                        collection_id=product.vector_collection_id,
                        limit=limit,
                        threshold=threshold
                    )
                    
                    if search_results["success"]:
                        for result in search_results["results"]:
                            result["product_info"] = {
                                "id": product.id,
                                "name": product.name,
                                "description": product.description,
                                "price": product.price,
                                "product_type": product.product_type
                            }
                            all_results.append(result)
            
            # Sort by similarity and limit results
            all_results.sort(key=lambda x: x["similarity"], reverse=True)
            all_results = all_results[:limit]
            
            return {
                "success": True,
                "query": query,
                "results": all_results,
                "total_found": len(all_results)
            }
            
        except Exception as e:
            logger.error(f"Error searching similar products: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("add_content_to_vector_index", args_schema=AddToVectorIndexInput)
    def add_content_to_vector_index(self, content: str, product_id: int, 
                                   content_type: str = "question") -> Dict[str, Any]:
        """Add content to vector index for future search."""
        try:
            if not self.vector_client:
                return {"success": False, "error": "Vector search client not available"}
            
            # Get product information
            db = next(get_db())
            product = db.query(Product).filter(Product.id == product_id).first()
            
            if not product:
                return {"success": False, "error": "Product not found"}
            
            if not product.vector_collection_id:
                return {"success": False, "error": "Product does not have a vector collection"}
            
            # Add content to vector index
            result = self.vector_client.add_document(
                content=content,
                collection_id=product.vector_collection_id,
                metadata={
                    "product_id": product_id,
                    "content_type": content_type,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            if result["success"]:
                # If it's a question, also store in AIQuestion table
                if content_type == "question":
                    # Extract question and answer if possible
                    parts = content.split("Answer:", 1)
                    question_text = parts[0].strip()
                    answer_text = parts[1].strip() if len(parts) > 1 else ""
                    
                    ai_question = AIQuestion(
                        product_id=product_id,
                        question=question_text,
                        answer=answer_text,
                        vector_id=result["vector_id"]
                    )
                    db.add(ai_question)
                    db.commit()
                
                logger.info(f"Added content to vector index for product {product_id}")
                return {
                    "success": True,
                    "vector_id": result["vector_id"],
                    "product_id": product_id,
                    "content_type": content_type,
                    "message": "Content added to vector index successfully"
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Error adding content to vector index: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("get_vector_collection_info", args_schema=dict)
    def get_vector_collection_info(self, product_id: int) -> Dict[str, Any]:
        """Get information about a product's vector collection."""
        try:
            if not self.vector_client:
                return {"success": False, "error": "Vector search client not available"}
            
            # Get product information
            db = next(get_db())
            product = db.query(Product).filter(Product.id == product_id).first()
            
            if not product:
                return {"success": False, "error": "Product not found"}
            
            if not product.vector_collection_id:
                return {
                    "success": True,
                    "product_id": product_id,
                    "has_vector_collection": False,
                    "message": "Product does not have a vector collection"
                }
            
            # Get collection information
            collection_info = self.vector_client.get_collection_info(
                collection_id=product.vector_collection_id
            )
            
            if collection_info["success"]:
                return {
                    "success": True,
                    "product_id": product_id,
                    "has_vector_collection": True,
                    "collection_id": product.vector_collection_id,
                    "collection_info": collection_info["info"]
                }
            else:
                return {"success": False, "error": collection_info["error"]}
                
        except Exception as e:
            logger.error(f"Error getting vector collection info: {e}")
            return {"success": False, "error": str(e)}
    
    @tool("semantic_product_search", args_schema=VectorSearchInput)
    def semantic_product_search(self, query: str, product_id: Optional[int] = None, 
                              limit: int = 5, threshold: float = 0.7) -> Dict[str, Any]:
        """Perform semantic search across all product content."""
        try:
            if not self.vector_client:
                return {"success": False, "error": "Vector search client not available"}
            
            # Get products to search
            db = next(get_db())
            if product_id:
                products = db.query(Product).filter(Product.id == product_id).all()
            else:
                products = db.query(Product).filter(
                    Product.is_active == True,
                    Product.vector_collection_id.isnot(None)
                ).all()
            
            if not products:
                return {
                    "success": True,
                    "query": query,
                    "results": [],
                    "total_found": 0,
                    "message": "No products found for search"
                }
            
            # Search across all products
            all_results = []
            for product in products:
                if product.vector_collection_id:
                    # Search product description
                    description_results = self.vector_client.search(
                        query=query,
                        collection_id=product.vector_collection_id,
                        limit=limit,
                        threshold=threshold
                    )
                    
                    if description_results["success"]:
                        for result in description_results["results"]:
                            result["product_info"] = {
                                "id": product.id,
                                "name": product.name,
                                "description": product.description,
                                "price": product.price,
                                "product_type": product.product_type
                            }
                            result["search_type"] = "product_description"
                            all_results.append(result)
                    
                    # Search AI questions for this product
                    questions = db.query(AIQuestion).filter(
                        AIQuestion.product_id == product.id
                    ).all()
                    
                    for question in questions:
                        if question.vector_id:
                            question_result = self.vector_client.search_by_id(
                                vector_id=question.vector_id,
                                query=query,
                                threshold=threshold
                            )
                            
                            if question_result["success"] and question_result["similarity"] >= threshold:
                                all_results.append({
                                    "similarity": question_result["similarity"],
                                    "content": question.question,
                                    "answer": question.answer,
                                    "product_info": {
                                        "id": product.id,
                                        "name": product.name,
                                        "description": product.description,
                                        "price": product.price,
                                        "product_type": product.product_type
                                    },
                                    "search_type": "ai_question",
                                    "question_id": question.id
                                })
            
            # Sort by similarity and limit results
            all_results.sort(key=lambda x: x["similarity"], reverse=True)
            all_results = all_results[:limit]
            
            return {
                "success": True,
                "query": query,
                "results": all_results,
                "total_found": len(all_results),
                "product_id": product_id
            }
            
        except Exception as e:
            logger.error(f"Error performing semantic product search: {e}")
            return {"success": False, "error": str(e)}
    
    def get_vector_analytics(self) -> Dict[str, Any]:
        """Get vector search analytics and statistics."""
        try:
            db = next(get_db())
            
            # Get product statistics
            total_products = db.query(Product).count()
            products_with_vectors = db.query(Product).filter(
                Product.vector_collection_id.isnot(None)
            ).count()
            
            # Get AI questions statistics
            total_questions = db.query(AIQuestion).count()
            questions_with_vectors = db.query(AIQuestion).filter(
                AIQuestion.vector_id.isnot(None)
            ).count()
            
            return {
                "success": True,
                "analytics": {
                    "total_products": total_products,
                    "products_with_vectors": products_with_vectors,
                    "vector_coverage": (products_with_vectors / total_products * 100) if total_products > 0 else 0,
                    "total_ai_questions": total_questions,
                    "questions_with_vectors": questions_with_vectors,
                    "question_vector_coverage": (questions_with_vectors / total_questions * 100) if total_questions > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting vector analytics: {e}")
            return {"success": False, "error": str(e)}
