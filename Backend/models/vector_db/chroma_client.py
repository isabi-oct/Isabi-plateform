import chromadb
from Backend.config.settings import settings
from typing import List, Dict, Any, Optional
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ChromaClient:
    """
    Optimized ChromaDB client for vector database operations.
    Handles product knowledge base storage and retrieval.
    """
    
    def __init__(self, db_path: str = "./chroma_db"):
        """
        Initialize ChromaDB client with persistent storage.
        
        Args:
            db_path: Path to store the ChromaDB database
        """
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            logger.info(f"ChromaDB client initialized with path: {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def create_collection(self, collection_name: str) -> Optional[str]:
        """
        Create a new collection for a product.
        
        Args:
            collection_name: Name of the collection to create
            
        Returns:
            Collection name if successful, None if failed
        """
        try:
            self.client.create_collection(
                name=collection_name,
                metadata={"description": f"Product knowledge base for {collection_name}"}
            )
            logger.info(f"Collection '{collection_name}' created successfully")
            return collection_name
        except Exception as e:
            logger.error(f"Error creating collection '{collection_name}': {e}")
            return None
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     metadatas: Optional[List[Dict]] = None) -> List[str]:
        """
        Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts to add
            metadatas: Optional list of metadata dictionaries
            
        Returns:
            List of document IDs if successful, empty list if failed
        """
        try:
            collection = self.client.get_collection(collection_name)
            ids = [str(uuid.uuid4()) for _ in documents]
            
            collection.add(
                documents=documents,
                metadatas=metadatas or [{"source": "product_db"} for _ in documents],
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents to collection '{collection_name}': {e}")
            return []
    
    def query_collection(self, collection_name: str, query_text: str, 
                        n_results: int = 5) -> Dict[str, Any]:
        """
        Query a collection for similar documents.
        
        Args:
            collection_name: Name of the collection to query
            query_text: Text to search for
            n_results: Number of results to return
            
        Returns:
            Dictionary containing query results
        """
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            logger.info(f"Query completed for collection '{collection_name}' with {len(results.get('documents', [[]])[0])} results")
            return results
        except Exception as e:
            logger.error(f"Error querying collection '{collection_name}': {e}")
            return {"documents": [], "metadatas": [], "distances": []}
    
    def get_collection(self, collection_name: str) -> Optional[Any]:
        """
        Get a collection by name.
        
        Args:
            collection_name: Name of the collection to retrieve
            
        Returns:
            Collection object if found, None if not found
        """
        try:
            collection = self.client.get_collection(collection_name)
            logger.info(f"Retrieved collection '{collection_name}'")
            return collection
        except Exception as e:
            logger.error(f"Error getting collection '{collection_name}': {e}")
            return None
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection by name.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if successful, False if failed
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Collection '{collection_name}' deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection '{collection_name}': {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        List all available collections.
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]
            logger.info(f"Found {len(collection_names)} collections")
            return collection_names
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []

# Global instance
chroma_client = ChromaClient()
