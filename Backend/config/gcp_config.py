"""
GCP Configuration Loader for Vector Search
"""

import os
import yaml
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv('Config/.env')

class GCPConfig:
    """GCP configuration manager"""
    
    def __init__(self, config_file: str = "Config/database_config.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def get_vector_config(self) -> Dict[str, Any]:
        """Get vector database configuration"""
        return self.config.get("vectordb", {})
    
    def get_project_id(self) -> str:
        """Get GCP project ID"""
        vector_config = self.get_vector_config()
        project_id = vector_config.get("project_id")
        
        # Expand environment variables
        if project_id and project_id.startswith("${") and project_id.endswith("}"):
            env_var = project_id[2:-1]
            project_id = os.getenv(env_var)
        
        return project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    
    def get_location(self) -> str:
        """Get GCP location/region"""
        vector_config = self.get_vector_config()
        return vector_config.get("location", "us-central1")
    
    def get_indexes(self) -> Dict[str, Dict[str, Any]]:
        """Get available indexes"""
        vector_config = self.get_vector_config()
        return vector_config.get("indexes", {})
    
    def get_default_index(self) -> str:
        """Get default index name"""
        vector_config = self.get_vector_config()
        return vector_config.get("default_index", "ai_product_index")
    
    def get_collections(self) -> Dict[str, str]:
        """Get collection mappings"""
        vector_config = self.get_vector_config()
        return vector_config.get("collections", {})
    
    def get_index_id(self, index_name: str) -> Optional[str]:
        """Get index ID by name"""
        indexes = self.get_indexes()
        if index_name in indexes:
            return indexes[index_name].get("id")
        return None

# Global instance
gcp_config = GCPConfig()
