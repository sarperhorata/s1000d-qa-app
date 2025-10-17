"""
Vector Store module for S1000D QA application
Provides abstraction for ChromaDB and FAISS vector stores
"""
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import numpy as np

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("ChromaDB not available. Install with: pip install chromadb")

from sentence_transformers import SentenceTransformer

from config import config


class VectorStore(ABC):
    """Abstract base class for vector stores"""
    
    @abstractmethod
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: Optional[List[str]] = None):
        """Add documents to the vector store"""
        pass
    
    @abstractmethod
    def search(self, query: str, k: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        pass
    
    @abstractmethod
    def delete_collection(self):
        """Delete the entire collection"""
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB-based vector store with persistence"""
    
    def __init__(
        self,
        collection_name: str = None,
        persist_directory: str = None,
        embedding_model: str = None
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is not installed. Install with: pip install chromadb")
        
        self.collection_name = collection_name or config.COLLECTION_NAME
        self.persist_directory = persist_directory or config.CHROMA_PERSIST_DIR
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL
        
        # Initialize embedding model
        print(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        print("Embedding model loaded successfully")
        
        # Initialize ChromaDB client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name
                )
                print(f"Loaded existing collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "S1000D document embeddings"}
                )
                print(f"Created new collection: {self.collection_name}")
            
        except Exception as e:
            print(f"Error initializing ChromaDB: {str(e)}")
            raise
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ):
        """Add documents to ChromaDB collection"""
        if not texts:
            return
        
        # Generate IDs if not provided
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(texts))]
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self._get_embeddings(texts)
        
        # Convert metadata to strings where necessary (ChromaDB requirement)
        clean_metadatas = []
        for metadata in metadatas:
            clean_meta = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    clean_meta[key] = value
                else:
                    clean_meta[key] = str(value)
            clean_metadatas.append(clean_meta)
        
        # Add to collection in batches
        batch_size = config.BATCH_SIZE
        for i in range(0, len(texts), batch_size):
            end_idx = min(i + batch_size, len(texts))
            
            self.collection.add(
                embeddings=embeddings[i:end_idx],
                documents=texts[i:end_idx],
                metadatas=clean_metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )
            print(f"Added batch {i//batch_size + 1}: {end_idx - i} documents")
        
        print(f"Successfully added {len(texts)} documents to collection")
    
    def search(
        self,
        query: str,
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents in ChromaDB"""
        # Generate query embedding
        query_embedding = self._get_embeddings([query])[0]
        
        # Build where clause for filtering
        where_clause = None
        if filter_dict:
            where_clause = filter_dict
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_clause
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                result = {
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'score': 1 - results['distances'][0][i] if results['distances'] else 0.0,  # Convert distance to similarity
                    'id': results['ids'][0][i] if results['ids'] else None
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def delete_collection(self):
        """Delete the collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_model_name
            }
        except Exception as e:
            print(f"Error getting collection stats: {str(e)}")
            return {}
    
    def update_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Update a document in the collection"""
        embedding = self._get_embeddings([text])[0]
        
        # Clean metadata
        clean_meta = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                clean_meta[key] = value
            else:
                clean_meta[key] = str(value)
        
        self.collection.update(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[clean_meta]
        )
        print(f"Updated document: {doc_id}")


class FAISSVectorStore(VectorStore):
    """FAISS-based vector store (legacy support)"""
    
    def __init__(self):
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        self.embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
        self.index = None
        print("FAISS vector store initialized (legacy mode)")
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: Optional[List[str]] = None):
        """Add documents to FAISS index"""
        from langchain_community.vectorstores import FAISS
        
        if self.index is None:
            self.index = FAISS.from_texts(texts=texts, embedding=self.embeddings, metadatas=metadatas)
        else:
            new_index = FAISS.from_texts(texts=texts, embedding=self.embeddings, metadatas=metadatas)
            self.index.merge_from(new_index)
        
        print(f"Added {len(texts)} documents to FAISS index")
    
    def search(self, query: str, k: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search FAISS index"""
        if self.index is None:
            return []
        
        results = self.index.similarity_search_with_score(query, k=k)
        
        formatted_results = []
        for doc, score in results:
            result = {
                'text': doc.page_content,
                'metadata': doc.metadata,
                'score': float(score)
            }
            formatted_results.append(result)
        
        return formatted_results
    
    def delete_collection(self):
        """Delete FAISS index"""
        self.index = None
        print("FAISS index cleared")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get FAISS index stats"""
        if self.index is None:
            return {"document_count": 0}
        
        return {
            "document_count": self.index.index.ntotal if hasattr(self.index, 'index') else 0,
            "type": "FAISS"
        }


def get_vector_store(store_type: str = None) -> VectorStore:
    """Factory function to get the appropriate vector store"""
    store_type = store_type or config.VECTOR_STORE_TYPE
    
    if store_type == "chromadb":
        if not CHROMADB_AVAILABLE:
            print("ChromaDB not available, falling back to FAISS")
            return FAISSVectorStore()
        return ChromaVectorStore()
    elif store_type == "faiss":
        return FAISSVectorStore()
    else:
        raise ValueError(f"Unknown vector store type: {store_type}")


# Test function
if __name__ == "__main__":
    # Test ChromaDB
    print("Testing ChromaDB vector store...")
    
    store = get_vector_store("chromadb")
    
    # Add test documents
    test_texts = [
        "S1000D is an international specification for technical publications",
        "Data modules are the basic building blocks of S1000D",
        "Business rules define validation constraints"
    ]
    test_metadatas = [
        {"page": 1, "chapter": "1.1", "type": "text"},
        {"page": 5, "chapter": "2.1", "type": "text"},
        {"page": 10, "chapter": "2.5", "type": "text"}
    ]
    
    store.add_documents(test_texts, test_metadatas)
    
    # Test search
    results = store.search("What is S1000D?", k=2)
    print("\nSearch results:")
    for result in results:
        print(f"Score: {result['score']:.3f} - {result['text'][:50]}...")
    
    # Get stats
    stats = store.get_collection_stats()
    print(f"\nCollection stats: {stats}")

