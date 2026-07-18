"""
RAG (Retrieval Augmented Generation) Service

Enables natural language querying over ingested data
using vector embeddings and LLM-powered responses.
"""
from typing import Any
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RAGService:
    """
    RAG pipeline:
    1. Embed documents into ChromaDB
    2. Retrieve relevant chunks for a query
    3. Generate answer using LLM with context
    """

    def __init__(self):
        self._chroma_client = None
        self._collection = None

    def _get_chroma(self):
        if not self._chroma_client:
            import chromadb
            self._chroma_client = chromadb.HttpClient(
                host=settings.CHROMADB_HOST,
                port=settings.CHROMADB_PORT,
            )
        return self._chroma_client

    def get_or_create_collection(self, collection_name: str):
        client = self._get_chroma()
        return client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def index_documents(
        self,
        documents: list[str],
        metadatas: list[dict],
        collection_name: str = "platform_docs",
    ) -> int:
        """Embed and store documents in ChromaDB."""
        collection = self.get_or_create_collection(collection_name)
        ids = [f"doc_{i}" for i in range(len(documents))]
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info("documents_indexed", count=len(documents), collection=collection_name)
        return len(documents)

    async def query(
        self,
        question: str,
        collection_name: str = "platform_docs",
        n_results: int = 5,
    ) -> dict[str, Any]:
        """Query the RAG pipeline with a natural language question."""
        collection = self.get_or_create_collection(collection_name)
        results = collection.query(query_texts=[question], n_results=n_results)

        context_docs = results.get("documents", [[]])[0]
        context = "\n\n".join(context_docs)

        if not settings.OPENAI_API_KEY:
            return {
                "answer": "LLM not configured. Retrieved context available.",
                "context": context_docs,
                "sources": results.get("metadatas", [[]])[0],
            }

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a data platform assistant. Answer questions based on the provided context. Be concise and accurate.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                },
            ],
            temperature=0.1,
            max_tokens=1024,
        )

        return {
            "answer": response.choices[0].message.content,
            "context": context_docs,
            "sources": results.get("metadatas", [[]])[0],
            "tokens_used": response.usage.total_tokens,
        }
