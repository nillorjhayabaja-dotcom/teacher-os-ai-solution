"""Vector Store — pgvector-backed RAG vector store."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class VectorStore:
    """pgvector-backed vector store for RAG.

    Uses HNSW indexing for fast approximate nearest neighbor search.
    All queries are tenant-scoped via RLS.

    Parameters
    ----------
    session:
        SQLAlchemy async session.  ``None`` makes the store a safe no-op
        (useful for component tests that verify wiring without a database).
    embedding_fn:
        Typed ``EmbeddingProvider`` used to embed queries before search.
    """

    def __init__(
        self,
        session: AsyncSession | None,
        embedding_fn: EmbeddingProvider,
    ) -> None:
        self._session = session
        self._embed = embedding_fn

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        tenant_id: UUID,
        *,
        top_k: int = 10,
        knowledge_types: Optional[List[str]] = None,
        min_score: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Semantic search for relevant knowledge chunks.

        Returns chunks ordered by similarity score (descending).
        Returns an empty list when no session is configured.
        """
        if not self._session:
            return []

        query_embedding = await self._embed.embed(query)

        sql = text("""
            SELECT id, content, metadata, knowledge_type,
                   1 - (embedding <=> :query_embedding::vector) AS similarity_score
            FROM ai_knowledge_chunks
            WHERE tenant_id = :tenant_id
              AND deleted_at IS NULL
              AND (:knowledge_types IS NULL OR knowledge_type = ANY(:knowledge_types))
              AND 1 - (embedding <=> :query_embedding::vector) > :min_score
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :top_k
        """)

        result = await self._session.execute(sql, {
            "query_embedding": str(query_embedding),
            "tenant_id": str(tenant_id),
            "knowledge_types": knowledge_types,
            "min_score": min_score,
            "top_k": top_k,
        })

        return [
            {
                "id": row.id,
                "content": row.content,
                "metadata": row.metadata,
                "knowledge_type": row.knowledge_type,
                "score": float(row.similarity_score),
            }
            for row in result.fetchall()
        ]

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    async def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        tenant_id: UUID,
    ) -> int:
        """Embed and store knowledge chunks.

        Returns the number of chunks persisted.  Returns ``0`` when no
        session is configured (component-test safety).
        """
        if not self._session:
            return 0

        count = 0
        for chunk in chunks:
            embedding = await self._embed.embed(chunk["content"])
            await self._session.execute(
                text("""
                    INSERT INTO ai_knowledge_chunks
                        (content, embedding, tenant_id, knowledge_type,
                         source_type, source_id, metadata, chunk_index, token_count)
                    VALUES
                        (:content, :embedding, :tenant_id, :knowledge_type,
                         :source_type, :source_id, :metadata, :chunk_index, :token_count)
                """),
                {
                    "content": chunk["content"],
                    "embedding": str(embedding),
                    "tenant_id": str(tenant_id),
                    "knowledge_type": chunk.get("knowledge_type", "general"),
                    "source_type": chunk.get("source_type", "manual"),
                    "source_id": str(chunk["source_id"]) if chunk.get("source_id") else None,
                    "metadata": str(chunk.get("metadata", {})),
                    "chunk_index": chunk.get("chunk_index", 0),
                    "token_count": chunk.get("token_count", 0),
                },
            )
            count += 1
        return count

    # ------------------------------------------------------------------
    # Delete (soft-delete)
    # ------------------------------------------------------------------

    async def delete_chunks(
        self,
        tenant_id: UUID,
        source_type: str,
        source_id: Optional[UUID] = None,
    ) -> int:
        """Soft-delete knowledge chunks by source.

        Returns the number of rows affected.
        """
        if not self._session:
            return 0

        params: Dict[str, Any] = {
            "tenant_id": str(tenant_id),
            "source_type": source_type,
        }
        where_extra = ""
        if source_id:
            where_extra = " AND source_id = :source_id"
            params["source_id"] = str(source_id)

        result = await self._session.execute(
            text(f"""
                UPDATE ai_knowledge_chunks
                SET deleted_at = now()
                WHERE tenant_id = :tenant_id
                  AND source_type = :source_type
                  {where_extra}
            """),
            params,
        )
        return result.rowcount