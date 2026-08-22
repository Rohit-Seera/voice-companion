"""Vector store infrastructure."""

from .client import qdrant_client
from .collections import CollectionManager, collections

__all__ = [
    "CollectionManager",
    "collections",
    "qdrant_client",
]
