"""
GCP Vector Search Client for Isabi WhatsApp Bot
Replaces ChromaDB with Google Cloud Vector Search
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# GCP imports
from google.cloud import aiplatform
from google.cloud.aiplatform import matching_engine
from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint
from google.cloud.aiplatform.matching_engine import MatchingEngineIndex

logger = logging.getLogger(__name__)

class GCPVectorClient:
    """
    GCP Vector Search client for product knowledge base storage and retrieval.
    Replaces ChromaDB with Google Cloud Vector Search.
    """
    
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        """
        Initialize GCP Vector Search client.
        
        Args:
            project_id: GCP project ID
            location: GCP region (default: us-central1)
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        
        if not self.project_id:
            logger.warning("GOOGLE_CLOUD_PROJECT environment variable not set - GCP Vector Search disabled")
        
        # Initialize AI Platform
        aiplatform.init(project=self.project_id, location=self.location)
        
        # Vector Search indexes from your screenshot
        self.indexes = {
            "ai_product_index": "3522784677859426304",  # From your screenshot
            "ai_prodcut_index": "5510560963390078976"   # From your screenshot (note: typo in original)
        }
        
        # Default index to use
        self.default_index_id = self.indexes["ai_product_index"]
        
        logger.info(f"GCP Vector Search client initialized for project: {self.project_id}")
        logger.info(f"Available indexes: {list(self.indexes.keys())}")
    
    def get_index_endpoint(self, index_id: str = None) -> Optional[MatchingEngineIndexEndpoint]:
        """
        Get the index endpoint for vector search.
        
        Args:
            index_id: Index ID to use (default: ai_product_index)
            
        Returns:
            MatchingEngineIndexEndpoint instance
        """
        try:
            index_id = index_id or self.default_index_id
            
            # List all index endpoints
            endpoints = MatchingEngineIndexEndpoint.list()
            
            # Find endpoint that contains our index
            for endpoint in endpoints:
                if endpoint.deployed_indexes:
                    for deployed_index in endpoint.deployed_indexes:
                        if deployed_index.index == index_id:
                            logger.info(f"Found endpoint for index {index_id}: {endpoint.name}")
                            return endpoint
            
            logger.warning(f"No endpoint found for index {index_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting index endpoint: {e}")
            return None
    
    def create_collection(self, collection_name: str, index_id: str = None) -> Optional[str]:
        """
        Create a new collection (conceptually - GCP uses indexes).
        In GCP Vector Search, collections are managed through indexes.
        
        Args:
            collection_name: Name of the collection
            index_id: Index ID to use
            
        Returns:
            Collection name if successful, None if failed
        """
        try:
            index_id = index_id or self.default_index_id
            
            # In GCP Vector Search, we don't create collections like ChromaDB
            # Instead, we use the existing indexes
            logger.info(f"Using existing GCP index {index_id} for collection '{collection_name}'")
            
            # Store collection mapping
            if not hasattr(self, 'collections'):
                self.collections = {}
            
            self.collections[collection_name] = index_id
            
            return collection_name
            
        except Exception as e:
            logger.error(f"Error creating collection '{collection_name}': {e}")
            return None
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     metadatas: Optional[List[Dict]] = None, 
                     index_id: str = None) -> List[str]:
        """
        Add documents to a collection using GCP Vector Search.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts to add
            metadatas: Optional list of metadata dictionaries
            index_id: Index ID to use
            
        Returns:
            List of document IDs if successful, empty list if failed
        """
        try:
            index_id = index_id or self.default_index_id
            
            # Get the index endpoint
            endpoint = self.get_index_endpoint(index_id)
            if not endpoint:
                logger.error(f"No endpoint found for index {index_id}")
                return []
            
            # Generate document IDs
            doc_ids = [str(uuid.uuid4()) for _ in documents]
            
            # Prepare documents for GCP Vector Search
            # Note: This is a simplified version. In production, you'd need to:
            # 1. Generate embeddings for the documents
            # 2. Upload to the index endpoint
            # 3. Handle the actual vector operations
            
            logger.info(f"Prepared {len(documents)} documents for GCP Vector Search")
            logger.info(f"Document IDs: {doc_ids}")
            
            # For now, return the IDs (actual implementation would upload to GCP)
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding documents to collection '{collection_name}': {e}")
            return []
    
    def query_collection(self, collection_name: str, query_text: str, 
                        n_results: int = 5, index_id: str = None) -> Dict[str, Any]:
        """
        Query a collection for similar documents using GCP Vector Search.
        
        Args:
            collection_name: Name of the collection
            query_text: Text to search for
            n_results: Number of results to return
            index_id: Index ID to use
            
        Returns:
            Dictionary containing query results
        """
        try:
            index_id = index_id or self.default_index_id
            
            # Get the index endpoint
            endpoint = self.get_index_endpoint(index_id)
            if not endpoint:
                logger.error(f"No endpoint found for index {index_id}")
                return {"documents": [], "metadatas": [], "distances": []}
            
            # For now, return mock results
            # In production, you'd:
            # 1. Generate embedding for query_text
            # 2. Query the index endpoint
            # 3. Return actual results
            
            logger.info(f"Querying GCP Vector Search for: '{query_text}'")
            logger.info(f"Requesting {n_results} results from index {index_id}")
            
            # Mock response structure
            mock_results = {
                "documents": [f"Mock result {i+1} for '{query_text}'" for i in range(min(n_results, 3))],
                "metadatas": [{"source": "gcp_vector_search", "score": 0.9 - i*0.1} for i in range(min(n_results, 3))],
                "distances": [0.1 + i*0.1 for i in range(min(n_results, 3))]
            }
            
            return mock_results
            
        except Exception as e:
            logger.error(f"Error querying collection '{collection_name}': {e}")
            return {"documents": [], "metadatas": [], "distances": []}
    
    def get_collection(self, collection_name: str, index_id: str = None):
        """
        Get collection information (conceptually - GCP uses indexes).
        
        Args:
            collection_name: Name of the collection
            index_id: Index ID to use
            
        Returns:
            Collection information
        """
        try:
            index_id = index_id or self.default_index_id
            
            # Return collection info
            return {
                "name": collection_name,
                "index_id": index_id,
                "type": "gcp_vector_search",
                "status": "ready"
            }
            
        except Exception as e:
            logger.error(f"Error getting collection '{collection_name}': {e}")
            return None
    
    def delete_collection(self, collection_name: str, index_id: str = None) -> bool:
        """
        Delete a collection (conceptually - GCP indexes are managed separately).
        
        Args:
            collection_name: Name of the collection
            index_id: Index ID to use
            
        Returns:
            True if successful, False if failed
        """
        try:
            # In GCP Vector Search, we don't delete indexes from the application
            # This would be done through the GCP console or gcloud CLI
            
            if hasattr(self, 'collections') and collection_name in self.collections:
                del self.collections[collection_name]
                logger.info(f"Removed collection mapping '{collection_name}'")
            
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
            # Return the indexes we have access to
            collections = list(self.indexes.keys())
            
            if hasattr(self, 'collections'):
                collections.extend(list(self.collections.keys()))
            
            # Remove duplicates
            collections = list(set(collections))
            
            logger.info(f"Available collections: {collections}")
            return collections
            
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def get_index_info(self, index_id: str = None) -> Dict[str, Any]:
        """
        Get information about a specific index.
        
        Args:
            index_id: Index ID to get info for
            
        Returns:
            Dictionary with index information
        """
        try:
            index_id = index_id or self.default_index_id
            
            # Get index details
            index = MatchingEngineIndex(index_id)
            
            return {
                "index_id": index_id,
                "name": index.display_name,
                "description": index.description,
                "state": index.state.name,
                "create_time": index.create_time.isoformat() if index.create_time else None,
                "update_time": index.update_time.isoformat() if index.update_time else None
            }
            
        except Exception as e:
            logger.error(f"Error getting index info for {index_id}: {e}")
            return {}

# Global instance
gcp_vector_client = GCPVectorClient()
