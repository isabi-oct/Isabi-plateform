"""
Products Catalog API

This module provides API endpoints for product management and catalog operations
integrated with the Agentic AI system.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from Backend.models.database.database import get_db
from Backend.models.database.models import Product, ProductType
from Backend.core.agents.product_agent import ProductAgent

router = APIRouter(tags=["Products"])
logger = logging.getLogger(__name__)

# Initialize product agent
product_agent = ProductAgent()

@router.get("/products")
async def get_all_products(
    limit: int = 10,
    offset: int = 0,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering."""
    try:
        query = db.query(Product).filter(Product.is_active == True)
        
        if category:
            query = query.filter(Product.product_type == category)
        
        products = query.offset(offset).limit(limit).all()
        
        product_list = []
        for product in products:
            product_list.append({
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "product_type": product.product_type,
                "is_active": product.is_active,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            })
        
        return {
            "status": "success",
            "products": product_list,
            "total": len(product_list),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get specific product by ID."""
    try:
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.is_active == True
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "status": "success",
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "product_type": product.product_type,
                "is_active": product.is_active,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/products/search")
async def search_products(
    query: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Search products using the Product Agent."""
    try:
        # Use Product Agent for intelligent search
        search_result = await product_agent.process({
            "user_id": "api_search",
            "message": query,
            "conversation_context": {"search_type": "api"}
        })
        
        if search_result.get("success"):
            return {
                "status": "success",
                "query": query,
                "products": search_result.get("products", []),
                "response": search_result.get("response", ""),
                "suggestions": search_result.get("suggestions", [])
            }
        else:
            raise HTTPException(status_code=400, detail=search_result.get("error", "Search failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/products/categories")
async def get_product_categories(db: Session = Depends(get_db)):
    """Get all product categories."""
    try:
        categories = db.query(Product.product_type).filter(
            Product.is_active == True,
            Product.product_type.isnot(None)
        ).distinct().all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return {
            "status": "success",
            "categories": category_list,
            "total": len(category_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/products/category/{category}")
async def get_products_by_category(
    category: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get products by category."""
    try:
        products = db.query(Product).filter(
            Product.product_type == category,
            Product.is_active == True
        ).limit(limit).all()
        
        product_list = []
        for product in products:
            product_list.append({
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "product_type": product.product_type,
                "is_active": product.is_active,
                "created_at": product.created_at.isoformat() if product.created_at else None
            })
        
        return {
            "status": "success",
            "category": category,
            "products": product_list,
            "total": len(product_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting products by category {category}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/products/recommendations")
async def get_product_recommendations(
    user_id: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get product recommendations using the Product Agent."""
    try:
        # Use Product Agent for recommendations
        recommendation_result = await product_agent.process({
            "user_id": user_id,
            "message": "recommend products for me",
            "conversation_context": {"recommendation_type": "api"}
        })
        
        if recommendation_result.get("success"):
            return {
                "status": "success",
                "user_id": user_id,
                "recommendations": recommendation_result.get("products", []),
                "response": recommendation_result.get("response", ""),
                "suggestions": recommendation_result.get("suggestions", [])
            }
        else:
            raise HTTPException(status_code=400, detail=recommendation_result.get("error", "Recommendation failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/products/agent/stats")
async def get_product_agent_stats():
    """Get Product Agent statistics."""
    try:
        stats = product_agent.get_product_stats()
        return {
            "status": "success",
            "agent_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting product agent stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")