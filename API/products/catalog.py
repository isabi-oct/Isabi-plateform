# Products Catalog API
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging

router = APIRouter(prefix="/products", tags=["Products Catalog"])
logger = logging.getLogger(__name__)

class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    currency: str
    category: str
    image_url: Optional[str] = None
    stock: int

class ProductResponse(BaseModel):
    products: List[Product]
    total_count: int
    page: int
    limit: int

@router.get("/", response_model=ProductResponse)
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Get products catalog with pagination and filtering"""
    try:
        logger.info(f"Getting products - page: {page}, limit: {limit}, category: {category}")
        
        # This will fetch from database
        products = [
            Product(
                id="prod_1",
                name="Digital Marketing Course",
                description="Complete digital marketing course",
                price=50000.0,
                currency="XAF",
                category="courses",
                stock=100
            ),
            Product(
                id="prod_2", 
                name="Web Development Bootcamp",
                description="Full-stack web development course",
                price=75000.0,
                currency="XAF",
                category="courses",
                stock=50
            )
        ]
        
        return ProductResponse(
            products=products,
            total_count=len(products),
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail="Failed to get products")

@router.get("/{product_id}")
async def get_product(product_id: str):
    """Get specific product by ID"""
    try:
        logger.info(f"Getting product: {product_id}")
        
        # This will fetch from database
        product = Product(
            id=product_id,
            name="Sample Product",
            description="Product description",
            price=50000.0,
            currency="XAF",
            category="courses",
            stock=100
        )
        
        return product
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        raise HTTPException(status_code=500, detail="Failed to get product")

@router.get("/search/")
async def search_products(q: str = Query(..., min_length=2)):
    """Search products by query"""
    try:
        logger.info(f"Searching products: {q}")
        
        # This will search in database
        return {
            "query": q,
            "products": [],
            "total_count": 0
        }
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail="Failed to search products")
