"""Document Chunker — splits documents into RAG-ready chunks."""

from __future__ import annotations

from typing import List


class DocumentChunker:
    """Splits documents into overlapping chunks for embedding and retrieval."""

    DEFAULT_CHUNK_SIZE = 512  # tokens
    DEFAULT_CHUNK_OVERLAP = 64  # tokens

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[dict]:
        words = text.split()
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(words):
            end = start + self._chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            chunks.append({
                "content": chunk_text,
                "chunk_index": chunk_index,
                "token_count": len(chunk_words),
                "start_offset": start,
                "end_offset": end,
            })
            chunk_index += 1
            start += self._chunk_size - self._chunk_overlap

        return chunks

    def chunk_document(self, content: str, metadata: dict) -> List[dict]:
        chunks = self.chunk_text(content)
        for chunk in chunks:
            chunk.update({
                "knowledge_type": metadata.get("knowledge_type", "general"),
                "source_type": metadata.get("source_type", "manual"),
                "source_id": metadata.get("source_id"),
                "title": metadata.get("title"),
                "tags": metadata.get("tags", []),
                "metadata": metadata.get("metadata", {}),
            })
        return chunks