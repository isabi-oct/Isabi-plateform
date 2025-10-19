"""
Product Agent for Agentic AI System

This agent specializes in product discovery, recommendations, and detailed product information.
It integrates with the database and vector search to provide accurate product data.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import psycopg2
from sqlalchemy.orm import Session

from .base_agent import BaseAgent
from Backend.models.database.database import get_db
from Backend.models.database.models import Product, ProductType
from ...Database.VectorDB.gcp_vector_client import gcp_vector_client

logger = logging.getLogger(__name__)

class ProductAgent(BaseAgent):
    """
    Agent responsible for product discovery, recommendations, and information.
    
    This agent handles all product-related queries including search, recommendations,
    detailed information, and category browsing.
    """
    
    def __init__(self):
        """Initialize the product agent."""
        super().__init__(
            agent_id="product",
            name="Product Agent",
            description="Handles product discovery, recommendations, and detailed information"
        )
        
        # Product categories and types
        self.product_categories = {
            'ai_courses': ['AI', 'Machine Learning', 'Artificial Intelligence', 'Deep Learning'],
            'digital_items': ['Digital', 'Software', 'E-book', 'Template', 'Tool'],
            'programming': ['Programming', 'Coding', 'Development', 'Software Engineering'],
            'design': ['Design', 'UI/UX', 'Graphic', 'Web Design', 'Creative'],
            'business': ['Business', 'Marketing', 'Entrepreneurship', 'Management']
        }
        
        # Search patterns
        self.search_patterns = {
            'category_search': ['category', 'type', 'kind', 'sort'],
            'price_search': ['price', 'cost', 'budget', 'affordable', 'expensive'],
            'skill_search': ['learn', 'skill', 'course', 'tutorial', 'training'],
            'specific_search': ['find', 'search', 'look for', 'need', 'want']
        }
        
        logger.info("Product Agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process product-related input and provide recommendations.
        
        Args:
            input_data: Input data containing user message and context
            
        Returns:
            Dictionary containing product recommendations and information
        """
        try:
            user_id = input_data.get('user_id')
            message = input_data.get('message', '')
            conversation_context = input_data.get('conversation_context', {})
            
            logger.info(f"Product Agent processing message from {user_id}: {message}")
            
            # Analyze product intent
            product_intent = self._analyze_product_intent(message)
            
            # Get products based on intent
            products = await self._get_products(product_intent, message, conversation_context)
            
            # Generate product response
            response = await self._generate_product_response(products, product_intent, message)
            
            # Get recommendations
            recommendations = await self._get_recommendations(products, conversation_context)
            
            result = {
                'success': True,
                'response': response,
                'products': products,
                'recommendations': recommendations,
                'product_intent': product_intent,
                'suggestions': self._get_product_suggestions(product_intent),
                'agents_used': ['product']
            }
            
            # Add to memory
            self.add_to_memory({
                'user_id': user_id,
                'message': message,
                'product_intent': product_intent,
                'products_found': len(products),
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Product Agent found {len(products)} products for intent '{product_intent}'")
            return result
            
        except Exception as e:
            logger.error(f"Error in Product Agent: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm having trouble finding products right now. Let me show you some popular options.",
                'products': await self._get_popular_products(),
                'suggestions': ['View All Products', 'Get Help', 'Contact Support']
            }
    
    def _analyze_product_intent(self, message: str) -> str:
        """
        Analyze message to determine product search intent.
        
        Args:
            message: User message
            
        Returns:
            Product intent
        """
        message_lower = message.lower()
        
        # Check for specific product search
        if any(pattern in message_lower for pattern in self.search_patterns['specific_search']):
            return 'specific_search'
        
        # Check for category search
        if any(pattern in message_lower for pattern in self.search_patterns['category_search']):
            return 'category_search'
        
        # Check for price-based search
        if any(pattern in message_lower for pattern in self.search_patterns['price_search']):
            return 'price_search'
        
        # Check for skill-based search
        if any(pattern in message_lower for pattern in self.search_patterns['skill_search']):
            return 'skill_search'
        
        # Check for category keywords
        for category, keywords in self.product_categories.items():
            if any(keyword.lower() in message_lower for keyword in keywords):
                return f'category_{category}'
        
        # Default to general search
        return 'general_search'
    
    async def _get_products(self, intent: str, message: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get products based on intent and message.
        
        Args:
            intent: Product search intent
            message: User message
            context: Conversation context
            
        Returns:
            List of product dictionaries
        """
        try:
            # Get database session
            db = next(get_db())
            
            if intent == 'specific_search':
                return await self._search_specific_products(message, db)
            elif intent.startswith('category_'):
                category = intent.replace('category_', '')
                return await self._get_products_by_category(category, db)
            elif intent == 'price_search':
                return await self._get_products_by_price(message, db)
            elif intent == 'skill_search':
                return await self._get_products_by_skill(message, db)
            else:
                return await self._get_popular_products(db)
                
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return await self._get_popular_products()
        finally:
            if 'db' in locals():
                db.close()
    
    async def _search_specific_products(self, message: str, db: Session) -> List[Dict[str, Any]]:
        """Search for specific products based on message content."""
        try:
            # Extract keywords from message
            keywords = self._extract_keywords(message)
            
            # Search in database
            products = db.query(Product).filter(
                Product.is_active == True,
                Product.name.ilike(f'%{keywords[0]}%') if keywords else True
            ).limit(5).all()
            
            # Convert to dictionaries
            product_list = []
            for product in products:
                product_list.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': product.price,
                    'product_type': product.product_type,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat() if product.created_at else None
                })
            
            return product_list
            
        except Exception as e:
            logger.error(f"Error in specific product search: {e}")
            return []
    
    async def _get_products_by_category(self, category: str, db: Session) -> List[Dict[str, Any]]:
        """Get products by category."""
        try:
            category_keywords = self.product_categories.get(category, [])
            
            # Build query
            query = db.query(Product).filter(Product.is_active == True)
            
            if category_keywords:
                # Search for category keywords in product name or description
                from sqlalchemy import or_
                conditions = []
                for keyword in category_keywords:
                    conditions.append(Product.name.ilike(f'%{keyword}%'))
                    conditions.append(Product.description.ilike(f'%{keyword}%'))
                query = query.filter(or_(*conditions))
            
            products = query.limit(5).all()
            
            # Convert to dictionaries
            product_list = []
            for product in products:
                product_list.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': product.price,
                    'product_type': product.product_type,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat() if product.created_at else None
                })
            
            return product_list
            
        except Exception as e:
            logger.error(f"Error getting products by category {category}: {e}")
            return []
    
    async def _get_products_by_price(self, message: str, db: Session) -> List[Dict[str, Any]]:
        """Get products filtered by price range."""
        try:
            # Extract price information from message
            price_range = self._extract_price_range(message)
            
            query = db.query(Product).filter(Product.is_active == True)
            
            if price_range['min'] is not None:
                query = query.filter(Product.price >= price_range['min'])
            if price_range['max'] is not None:
                query = query.filter(Product.price <= price_range['max'])
            
            products = query.order_by(Product.price).limit(5).all()
            
            # Convert to dictionaries
            product_list = []
            for product in products:
                product_list.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': product.price,
                    'product_type': product.product_type,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat() if product.created_at else None
                })
            
            return product_list
            
        except Exception as e:
            logger.error(f"Error getting products by price: {e}")
            return []
    
    async def _get_products_by_skill(self, message: str, db: Session) -> List[Dict[str, Any]]:
        """Get products related to specific skills."""
        try:
            # Extract skill keywords
            skill_keywords = self._extract_skill_keywords(message)
            
            query = db.query(Product).filter(Product.is_active == True)
            
            if skill_keywords:
                from sqlalchemy import or_
                conditions = []
                for keyword in skill_keywords:
                    conditions.append(Product.name.ilike(f'%{keyword}%'))
                    conditions.append(Product.description.ilike(f'%{keyword}%'))
                query = query.filter(or_(*conditions))
            
            products = query.limit(5).all()
            
            # Convert to dictionaries
            product_list = []
            for product in products:
                product_list.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': product.price,
                    'product_type': product.product_type,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat() if product.created_at else None
                })
            
            return product_list
            
        except Exception as e:
            logger.error(f"Error getting products by skill: {e}")
            return []
    
    async def _get_popular_products(self, db: Session = None) -> List[Dict[str, Any]]:
        """Get popular/featured products."""
        try:
            if db is None:
                db = next(get_db())
            
            products = db.query(Product).filter(
                Product.is_active == True
            ).order_by(Product.created_at.desc()).limit(5).all()
            
            # Convert to dictionaries
            product_list = []
            for product in products:
                product_list.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': product.price,
                    'product_type': product.product_type,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat() if product.created_at else None
                })
            
            return product_list
            
        except Exception as e:
            logger.error(f"Error getting popular products: {e}")
            return []
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extract search keywords from message."""
        # Simple keyword extraction
        words = message.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:3]  # Limit to 3 keywords
    
    def _extract_price_range(self, message: str) -> Dict[str, Optional[float]]:
        """Extract price range from message."""
        import re
        
        # Look for price patterns
        price_patterns = [
            r'under\s+\$?(\d+)',
            r'less\s+than\s+\$?(\d+)',
            r'below\s+\$?(\d+)',
            r'over\s+\$?(\d+)',
            r'more\s+than\s+\$?(\d+)',
            r'above\s+\$?(\d+)',
            r'\$?(\d+)\s*-\s*\$?(\d+)',
            r'between\s+\$?(\d+)\s+and\s+\$?(\d+)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, message.lower())
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    if 'under' in pattern or 'less' in pattern or 'below' in pattern:
                        return {'min': None, 'max': float(groups[0])}
                    else:
                        return {'min': float(groups[0]), 'max': None}
                elif len(groups) == 2:
                    return {'min': float(groups[0]), 'max': float(groups[1])}
        
        return {'min': None, 'max': None}
    
    def _extract_skill_keywords(self, message: str) -> List[str]:
        """Extract skill-related keywords from message."""
        skill_keywords = []
        message_lower = message.lower()
        
        # Common skill keywords
        skills = [
            'python', 'javascript', 'java', 'react', 'vue', 'angular',
            'machine learning', 'ai', 'artificial intelligence', 'data science',
            'web design', 'ui', 'ux', 'graphic design', 'photoshop',
            'marketing', 'seo', 'social media', 'content creation',
            'project management', 'leadership', 'communication'
        ]
        
        for skill in skills:
            if skill in message_lower:
                skill_keywords.append(skill)
        
        return skill_keywords
    
    async def _generate_product_response(self, products: List[Dict[str, Any]], intent: str, message: str) -> str:
        """Generate response based on found products."""
        if not products:
            return "I couldn't find any products matching your criteria. Let me show you some popular options instead! 🛍️"
        
        if len(products) == 1:
            product = products[0]
            return f"Perfect! I found this product for you: 🎯\n\n**{product['name']}**\n💰 Price: ${product['price']}\n📝 {product['description']}\n\nWould you like to know more about this product or see similar options?"
        
        # Multiple products
        product_names = [p['name'] for p in products[:3]]
        response = f"Great! I found {len(products)} products that match your search: 🎯\n\n"
        
        for i, product in enumerate(products[:3], 1):
            response += f"{i}. **{product['name']}** - ${product['price']}\n"
        
        if len(products) > 3:
            response += f"\n...and {len(products) - 3} more products!"
        
        response += "\n\nWhich product interests you most? I can provide more details or help you with the purchase process! 💫"
        
        return response
    
    async def _get_recommendations(self, products: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get additional product recommendations."""
        try:
            # Use vector search for recommendations if available
            if products and hasattr(gcp_vector_client, 'query_collection'):
                # Get recommendations based on first product
                first_product = products[0]
                query_text = f"{first_product['name']} {first_product['description']}"
                
                vector_results = gcp_vector_client.query_collection(
                    collection_name="isabi_products",
                    query_text=query_text,
                    n_results=3
                )
                
                if vector_results.get('documents'):
                    return vector_results['documents']
            
            # Fallback to similar products from database
            return await self._get_similar_products(products)
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def _get_similar_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get similar products from database."""
        try:
            if not products:
                return []
            
            # Get products from same category
            first_product = products[0]
            db = next(get_db())
            
            similar_products = db.query(Product).filter(
                Product.is_active == True,
                Product.id != first_product['id'],
                Product.product_type == first_product.get('product_type')
            ).limit(3).all()
            
            # Convert to dictionaries
            similar_list = []
            for product in similar_products:
                similar_list.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': product.price,
                    'product_type': product.product_type,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat() if product.created_at else None
                })
            
            return similar_list
            
        except Exception as e:
            logger.error(f"Error getting similar products: {e}")
            return []
    
    def _get_product_suggestions(self, intent: str) -> List[str]:
        """Get suggestion buttons based on product intent."""
        suggestions = {
            'specific_search': ['View Details', 'Similar Products', 'Add to Cart', 'Get Help'],
            'category_search': ['View All Categories', 'Popular Items', 'Price Range', 'Get Help'],
            'price_search': ['View Pricing', 'Payment Options', 'Order Now', 'Get Help'],
            'skill_search': ['Course Details', 'Learning Path', 'Pricing', 'Get Help'],
            'general_search': ['View All Products', 'Categories', 'Popular Items', 'Get Help']
        }
        
        return suggestions.get(intent, ['View Products', 'Get Help', 'Contact Support'])
    
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities.
        
        Returns:
            List of capability strings
        """
        return [
            'product_search',
            'product_recommendations',
            'category_browsing',
            'price_filtering',
            'skill_based_search',
            'product_details',
            'similar_products',
            'vector_search'
        ]
    
    def get_product_stats(self) -> Dict[str, Any]:
        """
        Get product agent statistics.
        
        Returns:
            Dictionary containing product stats
        """
        memory_items = self.get_memory(limit=100)
        
        # Count intents
        intent_counts = {}
        total_products_found = 0
        
        for item in memory_items:
            intent = item.get('product_intent', 'unknown')
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            total_products_found += item.get('products_found', 0)
        
        return {
            'total_searches': len(memory_items),
            'total_products_found': total_products_found,
            'intent_distribution': intent_counts,
            'average_products_per_search': total_products_found / len(memory_items) if memory_items else 0,
            'last_activity': self.last_activity.isoformat()
        }
