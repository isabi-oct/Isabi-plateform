# Vector Database Module - GCP Vector Search Only
from .gcp_vector_client import GCPVectorClient, gcp_vector_client

__all__ = [
    'GCPVectorClient',
    'gcp_vector_client'
]

# Default client (GCP Vector Search)
default_vector_client = gcp_vector_client
