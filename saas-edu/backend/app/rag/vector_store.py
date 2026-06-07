"""
RAG (Retrieval Augmented Generation) - Vector Store y Embeddings.
Maneja ChromaDB y sentence-transformers para embeddings locales.
"""

import os
import uuid
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

import httpx
from sentence_transformers import SentenceTransformer

from app.core.config import settings


@dataclass
class RetrievedChunk:
    """Fragmento de documento recuperado."""
    content: str
    chunk_id: str
    document_id: str
    page_number: Optional[int]
    score: float
    metadata: Dict[str, Any]


class ChromaManager:
    """
    Gestor de colecciones de ChromaDB por tenant.
    Implementa el patrón Singleton para mantener una sola conexión.
    """
    
    _instance: Optional['ChromaManager'] = None
    _client: Optional[Any] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._connect()
    
    def _connect(self):
        """Conecta a ChromaDB."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Usar cliente HTTP si Chroma está en otro contenedor
            chroma_host = os.getenv("CHROMA_HOST", settings.CHROMA_HOST)
            chroma_port = os.getenv("CHROMA_PORT", settings.CHROMA_PORT)
            
            self._client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port
            )
            print(f"✅ Conectado a ChromaDB en {chroma_host}:{chroma_port}")
            
        except Exception as e:
            print(f"⚠️  No se pudo conectar a ChromaDB: {e}")
            self._client = None
    
    @property
    def client(self):
        """Obtiene el cliente de ChromaDB."""
        if self._client is None:
            self._connect()
        return self._client
    
    def get_collection_name(self, tenant_id: str) -> str:
        """Genera nombre de colección para un tenant."""
        return f"tenant_{tenant_id}"
    
    def get_collection(self, tenant_id: str):
        """Obtiene o crea la colección de un tenant."""
        if self.client is None:
            return None
        
        collection_name = self.get_collection_name(tenant_id)
        
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"tenant_id": tenant_id}
            )
            return collection
        except Exception as e:
            print(f"Error al obtener colección: {e}")
            return None
    
    def reset_tenant(self, tenant_id: str) -> bool:
        """Elimina todos los vectores de un tenant."""
        if self.client is None:
            return False
        
        collection_name = self.get_collection_name(tenant_id)
        
        try:
            self.client.delete_collection(name=collection_name)
            print(f"🗑️ Colección '{collection_name}' eliminada")
            return True
        except Exception as e:
            print(f"Error al eliminar colección: {e}")
            return False
    
    def get_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas de la colección de un tenant."""
        collection = self.get_collection(tenant_id)
        if collection is None:
            return {"count": 0, "error": "No se pudo acceder a la colección"}
        
        try:
            return {
                "count": collection.count(),
                "collection_name": collection.name
            }
        except Exception as e:
            return {"count": 0, "error": str(e)}


class EmbeddingService:
    """
    Servicio de embeddings usando sentence-transformers.
    Carga el modelo una sola vez y lo reutiliza.
    """
    
    _instance: Optional['EmbeddingService'] = None
    _model: Optional[SentenceTransformer] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Carga el modelo de embeddings."""
        model_name = settings.EMBEDDING_MODEL
        print(f"📦 Cargando modelo de embeddings: {model_name}...")
        
        try:
            self._model = SentenceTransformer(model_name)
            print(f"✅ Modelo '{model_name}' cargado exitosamente")
        except Exception as e:
            print(f"❌ Error al cargar modelo: {e}")
            self._model = None
    
    @property
    def model(self) -> Optional[SentenceTransformer]:
        """Obtiene el modelo."""
        if self._model is None:
            self._load_model()
        return self._model
    
    @property
    def embedding_dim(self) -> int:
        """Dimensión de los embeddings (para crear colección)."""
        return 384  # all-MiniLM-L6-v2 produce embeddings de 384 dims
    
    def encode(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Genera embeddings para una lista de textos.
        
        Args:
            texts: Lista de textos a embeber
            
        Returns:
            Lista de embeddings o None si falla
        """
        if self.model is None:
            return None
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            print(f"Error al generar embeddings: {e}")
            return None
    
    def encode_query(self, query: str) -> Optional[List[float]]:
        """
        Genera embedding para una consulta.
        
        Args:
            query: Texto de la consulta
            
        Returns:
            Embedding o None si falla
        """
        result = self.encode([query])
        return result[0] if result else None


class RetrievalPipeline:
    """
    Pipeline de recuperación de documentos.
    Combina ChromaDB y EmbeddingService para RAG.
    """
    
    def __init__(self):
        self.chroma = ChromaManager()
        self.embedder = EmbeddingService()
    
    def add_documents(
        self,
        tenant_id: str,
        chunks: List[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        """
        Añade documentos a ChromaDB.
        
        Args:
            tenant_id: ID del tenant
            chunks: Lista de dicts con {content, document_id, chunk_index, page_number}
            
        Returns:
            (num_chunks_added, list_of_vector_ids)
        """
        if not chunks:
            return 0, []
        
        collection = self.chroma.get_collection(tenant_id)
        if collection is None:
            raise Exception("No se pudo acceder a ChromaDB")
        
        # Generar embeddings
        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.embedder.encode(texts)
        
        if embeddings is None:
            raise Exception("Error al generar embeddings")
        
        # Preparar datos para ChromaDB
        ids = []
        documents = []
        metadatas = []
        vectors = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{chunk['document_id']}_{chunk['chunk_index']}"
            ids.append(chunk_id)
            documents.append(chunk["content"])
            metadatas.append({
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "page_number": chunk.get("page_number"),
                "tenant_id": tenant_id
            })
            vectors.append(embeddings[i])
        
        # Añadir a ChromaDB
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=vectors
        )
        
        print(f"✅ Añadidos {len(chunks)} chunks a ChromaDB")
        return len(chunks), ids
    
    def retrieve(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5,
        filter_document_id: Optional[str] = None
    ) -> List[RetrievedChunk]:
        """
        Recupera los chunks más relevantes para una consulta.
        
        Args:
            tenant_id: ID del tenant
            query: Texto de la consulta
            top_k: Número de chunks a recuperar
            filter_document_id: Filtrar por documento específico
            
        Returns:
            Lista de RetrievedChunk ordenados por relevancia
        """
        collection = self.chroma.get_collection(tenant_id)
        if collection is None:
            return []
        
        # Generar embedding de la consulta
        query_embedding = self.embedder.encode_query(query)
        if query_embedding is None:
            return []
        
        # Preparar filtros
        where_filter = None
        if filter_document_id:
            where_filter = {"document_id": filter_document_id}
        
        # Query a ChromaDB
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print(f"Error en query de ChromaDB: {e}")
            return []
        
        # Parsear resultados
        retrieved_chunks = []
        
        if results and results.get("ids"):
            for i, chunk_id in enumerate(results["ids"][0]):
                retrieved = RetrievedChunk(
                    content=results["documents"][0][i],
                    chunk_id=chunk_id,
                    document_id=results["metadatas"][0][i].get("document_id", ""),
                    page_number=results["metadatas"][0][i].get("page_number"),
                    score=1 - results["distances"][0][i],  # Convertir distancia a similitud
                    metadata=results["metadatas"][0][i]
                )
                retrieved_chunks.append(retrieved)
        
        return retrieved_chunks
    
    def delete_document_vectors(self, tenant_id: str, document_id: str) -> bool:
        """
        Elimina todos los vectores de un documento.
        
        Args:
            tenant_id: ID del tenant
            document_id: ID del documento
            
        Returns:
            True si éxito, False si falla
        """
        collection = self.chroma.get_collection(tenant_id)
        if collection is None:
            return False
        
        try:
            # Buscar todos los chunks del documento
            results = collection.get(
                where={"document_id": document_id},
                include=["ids"]
            )
            
            if results and results.get("ids"):
                collection.delete(ids=results["ids"])
                print(f"🗑️ Eliminados {len(results['ids'])} vectores del documento {document_id}")
            
            return True
        except Exception as e:
            print(f"Error al eliminar vectores: {e}")
            return False
    
    def retrieve_for_evaluation(
        self,
        tenant_id: str,
        document_id: str,
        count: int = 10
    ) -> List[str]:
        """
        Recupera chunks para generar preguntas de evaluación.
        Selecciona chunks distribuidos por todo el documento.
        
        Args:
            tenant_id: ID del tenant
            document_id: ID del documento
            count: Número de chunks a recuperar
            
        Returns:
            Lista de contenidos de chunks
        """
        collection = self.chroma.get_collection(tenant_id)
        if collection is None:
            return []
        
        try:
            # Obtener todos los chunks del documento
            results = collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )
            
            if not results or not results.get("documents"):
                return []
            
            # Seleccionar chunks distribuidos uniformemente
            chunks = results["documents"]
            total_chunks = len(chunks)
            
            if total_chunks <= count:
                return chunks
            
            # Seleccionar cada nth chunk
            step = total_chunks / count
            selected = []
            
            for i in range(count):
                idx = int(i * step)
                if idx < total_chunks:
                    selected.append(chunks[idx])
            
            return selected
            
        except Exception as e:
            print(f"Error al recuperar chunks para evaluación: {e}")
            return []


# Instancias globales (singleton)
chroma_manager = ChromaManager()
embedding_service = EmbeddingService()
retrieval_pipeline = RetrievalPipeline()