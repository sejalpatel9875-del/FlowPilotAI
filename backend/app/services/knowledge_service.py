import json
import math
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.knowledge import DocumentModel, DocumentChunkModel
from app.services.text_extractor import TextExtractor
from app.services.llm_service import LLMService
from app.services.security_guard_service import SensitiveDataFilter
from app.services.llm.base_provider import LLMRequest

logger = logging.getLogger("flowpilot.knowledge_service")


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class KnowledgeService:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 600, overlap: int = 120) -> List[str]:
        """Splits extracted text into overlapping semantic chunks."""
        clean_text = text.strip()
        if not clean_text:
            return []
        if len(clean_text) <= chunk_size:
            return [clean_text]

        chunks = []
        start = 0
        while start < len(clean_text):
            end = min(start + chunk_size, len(clean_text))
            if end < len(clean_text):
                boundary = clean_text.rfind("\n", start, end)
                if boundary == -1 or boundary <= start:
                    boundary = clean_text.rfind(" ", start, end)
                if boundary > start:
                    end = boundary

            chunk = clean_text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap if end - overlap > start else end

        return chunks

    @classmethod
    async def ingest_document(
        cls,
        user_id: str,
        filename: str,
        file_bytes: bytes,
        content_type: Optional[str],
        db: AsyncSession
    ) -> DocumentModel:
        """Ingest PDF/Notes/Docs: Text Extraction -> Chunking -> NVIDIA Embeddings -> Vector DB."""
        # 1. Text Extraction
        extracted_text = TextExtractor.extract_text(file_bytes, filename, content_type)
        sanitized_text, _ = SensitiveDataFilter.redact_sensitive_data(extracted_text)

        # 2. Document Model Creation
        doc_id = str(uuid.uuid4())
        ext = filename.lower().split(".")[-1] if "." in filename else "text"
        doc = DocumentModel(
            id=doc_id,
            user_id=user_id,
            title=filename,
            file_type=ext,
            storage_path=f"vault/{user_id}/{doc_id}_{filename}",
            checksum=str(len(file_bytes))
        )
        db.add(doc)
        await db.flush()

        # 3. Semantic Chunking
        chunks = cls.chunk_text(sanitized_text)

        # 4. NVIDIA Embeddings & Vector Storage
        created_chunks = []
        for idx, chunk_text in enumerate(chunks):
            embedding_vector = await LLMService.embed(chunk_text, provider_name="nvidia")
            chunk_obj = DocumentChunkModel(
                id=str(uuid.uuid4()),
                document_id=doc.id,
                user_id=user_id,
                chunk_index=idx,
                content_text=chunk_text,
                embedding_json=json.dumps(embedding_vector)
            )
            db.add(chunk_obj)
            created_chunks.append(chunk_obj)

        await db.commit()
        await db.refresh(doc)
        return doc

    @classmethod
    async def process_document_upload(
        cls,
        user_id: str,
        file_name: str,
        file_bytes: bytes,
        file_type: Optional[str],
        db: AsyncSession
    ) -> DocumentModel:
        """Alias for upload endpoint."""
        return await cls.ingest_document(user_id, file_name, file_bytes, file_type, db)

    @classmethod
    async def hybrid_search_and_rerank(
        cls,
        user_id: str,
        query: str,
        db: AsyncSession,
        top_k: int = 5
    ) -> List[Tuple[DocumentChunkModel, DocumentModel, float]]:
        """Hybrid Keyword + Vector Cosine Search & Re-ranking pipeline."""
        query_vector = await LLMService.embed(query, provider_name="nvidia")
        query_terms = [t.lower() for t in query.split() if len(t) > 2]

        res = await db.execute(
            select(DocumentChunkModel, DocumentModel)
            .join(DocumentModel, DocumentChunkModel.document_id == DocumentModel.id)
            .where(
                DocumentChunkModel.user_id == user_id,
                DocumentModel.is_deleted == False
            )
        )
        records = res.all()

        scored_candidates = []
        for chunk, doc in records:
            vector = json.loads(chunk.embedding_json) if chunk.embedding_json else []
            vec_score = _cosine_similarity(query_vector, vector)

            content_lower = chunk.content_text.lower()
            kw_matches = sum(1 for term in query_terms if term in content_lower)
            kw_score = (kw_matches / len(query_terms)) if query_terms else 0.0

            final_score = (0.7 * vec_score) + (0.3 * kw_score)
            scored_candidates.append((chunk, doc, round(final_score, 4)))

        scored_candidates.sort(key=lambda x: x[2], reverse=True)
        return scored_candidates[:top_k]

    @classmethod
    async def hybrid_vector_search(
        cls,
        query: str,
        user_id: str,
        db: AsyncSession,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """API Search helper returning dict results."""
        results = await cls.hybrid_search_and_rerank(user_id, query, db, top_k)
        return [
            {
                "documentId": doc.id,
                "documentTitle": doc.title,
                "chunkIndex": chunk.chunk_index,
                "contentText": chunk.content_text,
                "relevanceScore": score
            }
            for chunk, doc, score in results
        ]

    @classmethod
    async def query_knowledge_vault(
        cls,
        user_id: str,
        query: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Full RAG Pipeline: Hybrid Retrieval -> Re-ranking -> Nemotron 3 Ultra -> Answer + Citations."""
        ranked_chunks = await cls.hybrid_search_and_rerank(user_id, query, db, top_k=4)

        if not ranked_chunks:
            return {
                "query": query,
                "answer": "No relevant documents found in your Knowledge Vault to answer this query. Upload notes, PDFs, or docs to ingest context.",
                "citations": [],
                "hasRelevantDocs": False,
                "retrievedChunksCount": 0
            }

        context_blocks = []
        citations = []

        for idx, (chunk, doc, score) in enumerate(ranked_chunks):
            context_blocks.append(f"[Source {idx + 1}: {doc.title} (Chunk #{chunk.chunk_index + 1})]\n{chunk.content_text}")
            citations.append({
                "sourceId": idx + 1,
                "documentId": doc.id,
                "documentTitle": doc.title,
                "chunkIndex": chunk.chunk_index,
                "relevanceScore": score,
                "excerpt": chunk.content_text[:200] + "..." if len(chunk.content_text) > 200 else chunk.content_text
            })

        formatted_context = "\n\n".join(context_blocks)
        system_prompt = (
            "You are Nemotron 3 Ultra, FlowPilot AI's production RAG Knowledge Vault assistant. "
            "Synthesize a clear, accurate, and professional answer strictly based on the provided context sources. "
            "Cite sources explicitly in your response using [Source X] references. Do not hallucinate information."
        )

        user_prompt = f"Retrieved Vault Context:\n{formatted_context}\n\nUser Question:\n{query}"

        rag_req = LLMRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model="nvidia/nemotron-3-ultra-550b-a55b",
            temperature=0.3
        )

        res = await LLMService.generate(
            req=rag_req,
            user_id=user_id,
            db=db,
            provider_name="nvidia"
        )

        return {
            "query": query,
            "answer": res.text,
            "citations": citations,
            "hasRelevantDocs": True,
            "retrievedChunksCount": len(ranked_chunks),
            "provider": res.provider,
            "model": res.model,
            "usage": {
                "inputTokens": res.usage.input_tokens,
                "outputTokens": res.usage.output_tokens,
                "totalTokens": res.usage.total_tokens,
            }
        }

    @classmethod
    async def rag_chat_query(
        cls,
        query: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Alias for RAG Q&A endpoint."""
        return await cls.query_knowledge_vault(user_id, query, db)

    @classmethod
    async def get_user_documents(cls, user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
        """Retrieve user's ingested documents with chunk metrics."""
        res = await db.execute(
            select(DocumentModel)
            .where(
                DocumentModel.user_id == user_id,
                DocumentModel.is_deleted == False
            )
            .order_by(DocumentModel.created_at.desc())
        )
        docs = res.scalars().all()

        result = []
        for doc in docs:
            chunk_res = await db.execute(
                select(DocumentChunkModel).where(DocumentChunkModel.document_id == doc.id)
            )
            chunks = chunk_res.scalars().all()
            result.append({
                "id": doc.id,
                "title": doc.title,
                "fileType": doc.file_type,
                "totalChunks": len(chunks),
                "createdAt": doc.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            })

        return result

    @classmethod
    async def delete_document(cls, document_id: str, user_id: str, db: AsyncSession) -> bool:
        """Soft delete document strictly scoped to user_id."""
        res = await db.execute(
            select(DocumentModel).where(
                DocumentModel.id == document_id,
                DocumentModel.user_id == user_id,
                DocumentModel.is_deleted == False
            )
        )
        doc = res.scalar_one_or_none()
        if not doc:
            return False

        doc.is_deleted = True
        await db.commit()
        return True


knowledge_service = KnowledgeService()
