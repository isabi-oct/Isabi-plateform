# Vector Database Module - Updated for GCP Vector Search
from .gcp_vector_client import GCPVectorClient, gcp_vector_client

# Keep ChromaDB for backward compatibility (optional)
try:
    from .chroma_client import ChromaClient
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

__all__ = [
    'GCPVectorClient',
    'gcp_vector_client'
]

# Add ChromaDB if available
if CHROMADB_AVAILABLE:
    __all__.extend(['ChromaClient'])

# Default client (GCP Vector Search)
default_vector_client = gcp_vector_client
