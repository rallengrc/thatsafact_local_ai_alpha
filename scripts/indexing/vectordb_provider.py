"""
vectordb_provider.py — Pluggable vector database provider abstraction.

Defines the interface for different vector database implementations.
Supports chromadb, OpenAI embeddings, and other providers via simple inheritance.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


class VectorDBProvider(ABC):
    """Base class for vector database providers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider.

        Args:
            config: Dictionary with provider-specific configuration.
        """
        self.config = config

    @abstractmethod
    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        collection_name: str = "documents",
    ) -> int:
        """
        Index a batch of documents.

        Args:
            documents: List of dicts with 'id', 'text', and optional 'metadata'.
            collection_name: Name of the collection/index.

        Returns:
            Number of documents indexed.
        """
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        collection_name: str = "documents",
        limit: int = 10,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.

        Args:
            query: Search query text.
            collection_name: Name of the collection/index.
            limit: Maximum number of results.
            threshold: Optional similarity threshold (0-1).

        Returns:
            List of results with 'id', 'text', 'distance', and 'metadata'.
        """
        pass

    @abstractmethod
    def clear_collection(self, collection_name: str = "documents") -> None:
        """
        Clear all documents from a collection.

        Args:
            collection_name: Name of the collection/index.
        """
        pass

    @abstractmethod
    def get_stats(self, collection_name: str = "documents") -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Args:
            collection_name: Name of the collection/index.

        Returns:
            Dictionary with stats (document count, etc.).
        """
        pass


class ChromaDBProvider(VectorDBProvider):
    """ChromaDB vector database provider."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ChromaDB provider.

        Args:
            config: Must include 'db_path' (local persistent directory).
        """
        super().__init__(config)
        import chromadb

        raw_path = config.get("db_path", ".chroma")
        # Unwrap nested dictionaries if accidentally passed
        while isinstance(raw_path, dict):
            raw_path = raw_path.get("db_path", ".chroma")

        if isinstance(raw_path, Path):
            raw_path = str(raw_path)
        elif not isinstance(raw_path, str):
            raw_path = str(raw_path)

        # Defensive check against stringified Python dictionary paths
        if raw_path.strip().startswith("{") and raw_path.strip().endswith("}"):
            raise ValueError(f"Invalid db_path '{raw_path}': appears to be a stringified dictionary.")

        self.db_path = os.path.abspath(raw_path) if not raw_path.startswith(".") else raw_path
        self.client = chromadb.PersistentClient(path=self.db_path)
        logger.info(f"ChromaDB initialized at {self.db_path}")

    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        collection_name: str = "documents",
    ) -> int:
        """Index documents into ChromaDB."""
        if not documents:
            return 0

        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        ids = []
        texts = []
        metadatas = []

        for doc in documents:
            ids.append(doc["id"])
            texts.append(doc["text"])
            # ChromaDB requires non-empty metadata dict
            metadata = doc.get("metadata", {})
            if not metadata:
                metadata = {"_source": "indexed"}
            metadatas.append(metadata)

        collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        logger.info(f"Indexed {len(documents)} documents into '{collection_name}'")
        return len(documents)

    def search(
        self,
        query: str,
        collection_name: str = "documents",
        limit: int = 10,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search ChromaDB collection."""
        collection = self.client.get_or_create_collection(name=collection_name)

        results = collection.query(query_texts=[query], n_results=limit)

        output = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance
                if threshold is None or similarity >= threshold:
                    output.append(
                        {
                            "id": doc_id,
                            "text": results["documents"][0][i],
                            "similarity": similarity,
                            "distance": distance,
                            "metadata": results["metadatas"][0][i],
                        }
                    )

        return output

    def clear_collection(self, collection_name: str = "documents") -> None:
        """Clear a ChromaDB collection."""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Cleared collection '{collection_name}'")
        except (ValueError, Exception):
            logger.debug(f"Collection '{collection_name}' does not exist or already cleared")

    def get_stats(self, collection_name: str = "documents") -> Dict[str, Any]:
        """Get ChromaDB collection statistics."""
        collection = self.client.get_or_create_collection(name=collection_name)
        count = collection.count()
        return {"document_count": count, "collection_name": collection_name}


def get_provider(provider_name: str, config: Dict[str, Any]) -> VectorDBProvider:
    """
    Factory function to get a vector database provider.

    Args:
        provider_name: Name of provider ('chromadb', 'openai', etc.).
        config: Provider-specific configuration.

    Returns:
        Initialized provider instance.
    """
    providers = {
        "chromadb": ChromaDBProvider,
    }

    if provider_name not in providers:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Supported: {list(providers.keys())}"
        )

    provider_class = providers[provider_name]
    return provider_class(config)
