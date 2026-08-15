from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.knowledge import DocumentModel, DocumentChunkModel
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


class SearchQueryRequest(BaseModel):
    query: str = Field(..., description="Semantic search query text")
    topK: int = Field(default=4, description="Top K chunk results")


class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="User RAG question text")


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Authenticated document ingestion endpoint (PDF, TXT, MD, Notes)."""
    try:
        file_bytes = await file.read()
        doc = await KnowledgeService.process_document_upload(
            user_id=user.id,
            file_name=file.filename or "document.txt",
            file_bytes=file_bytes,
            file_type=file.content_type or "text/plain",
            db=db,
        )

        chunk_res = await db.execute(
            select(DocumentChunkModel).where(DocumentChunkModel.document_id == doc.id)
        )
        chunks = chunk_res.scalars().all()

        return {
            "id": doc.id,
            "title": doc.title,
            "fileType": doc.file_type,
            "chunkCount": len(chunks),
            "status": "indexed",
            "createdAt": doc.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.post("/query")
async def query_knowledge_vault(
    req: RAGQueryRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Full Production RAG Pipeline: Hybrid Search → Re-ranking → Nemotron 3 Ultra → Answer + Citations."""
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty.")

    return await KnowledgeService.query_knowledge_vault(
        user_id=user.id,
        query=req.query,
        db=db
    )


@router.get("/documents")
async def list_documents(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List authenticated user's uploaded documents with chunk statistics."""
    res = await db.execute(
        select(DocumentModel)
        .where(
            DocumentModel.user_id == user.id,
            DocumentModel.is_deleted == False
        )
        .order_by(DocumentModel.created_at.desc())
    )
    docs = res.scalars().all()

    items = []
    for doc in docs:
        c_res = await db.execute(
            select(DocumentChunkModel).where(DocumentChunkModel.document_id == doc.id)
        )
        chunks = c_res.scalars().all()
        items.append({
            "id": doc.id,
            "title": doc.title,
            "fileType": doc.file_type,
            "chunkCount": len(chunks),
            "status": "indexed",
            "createdAt": doc.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        })

    return {"documents": items}


@router.get("/documents/{document_id}")
async def get_document_details(
    document_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """View document details and text chunks with strict ownership check."""
    doc_res = await db.execute(
        select(DocumentModel).where(
            DocumentModel.id == document_id,
            DocumentModel.user_id == user.id,
            DocumentModel.is_deleted == False
        )
    )
    doc = doc_res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized.")

    chunk_res = await db.execute(
        select(DocumentChunkModel)
        .where(DocumentChunkModel.document_id == doc.id)
        .order_by(DocumentChunkModel.chunk_index.asc())
    )
    chunks = chunk_res.scalars().all()

    return {
        "id": doc.id,
        "title": doc.title,
        "fileType": doc.file_type,
        "createdAt": doc.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "chunks": [
            {
                "chunkIndex": c.chunk_index,
                "contentText": c.content_text,
            }
            for c in chunks
        ]
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete document and its chunks with strict ownership check."""
    success = await KnowledgeService.delete_document(document_id, user.id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized.")

    return {"status": "success", "message": f"Document deleted successfully."}


@router.post("/search")
async def hybrid_search_chunks(
    req: SearchQueryRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hybrid semantic vector & keyword search endpoint with tenant isolation."""
    results = await KnowledgeService.hybrid_vector_search(
        query=req.query,
        user_id=user.id,
        db=db,
        top_k=req.topK
    )
    return {"results": results}


@router.post("/chat")
async def rag_chat_question(
    req: RAGQueryRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """RAG Q&A endpoint returning answer, source citations, and relevance scores."""
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    return await KnowledgeService.rag_chat_query(
        query=req.query,
        user_id=user.id,
        db=db
    )
