import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.knowledge_service import KnowledgeService
from app.models.user import UserModel
from app.core.security import hash_password

@pytest.mark.asyncio
async def test_text_chunker():
    sample_text = (
        "Paragraph 1: FlowPilot AI is an AI-powered Freelancing, Growth, Productivity and Learning Operating System. "
        "It automates repetitive workflows.\n\n"
        "Paragraph 2: The RAG Knowledge Vault allows users to upload PDF, TXT, and Markdown files. "
        "It performs text extraction, chunking, and multi-tenant vector retrieval."
    )
    chunks = KnowledgeService.chunk_text(sample_text, chunk_size=150, overlap=30)
    assert len(chunks) >= 2
    assert "FlowPilot AI" in chunks[0]

@pytest.mark.asyncio
async def test_document_ingestion_and_tenant_isolation(db_session: AsyncSession):
    # Create User A & User B
    user_a = UserModel(email="usera@flowpilot.ai", password_hash=hash_password("Pass123!"), full_name="User A")
    user_b = UserModel(email="userb@flowpilot.ai", password_hash=hash_password("Pass123!"), full_name="User B")
    db_session.add(user_a)
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    # Ingest document for User A
    doc_a = await KnowledgeService.process_document_upload(
        user_id=user_a.id,
        file_name="client_contract_user_a.txt",
        file_bytes=b"Confidential project budget for User A is $50,000 USD for Q4 deliverables.",
        file_type="text/plain",
        db=db_session
    )
    assert doc_a.id is not None

    # 1. Search for User A -> Should return chunk
    results_a = await KnowledgeService.hybrid_vector_search(
        query="project budget deliverables",
        user_id=user_a.id,
        db=db_session
    )
    assert len(results_a) == 1
    assert "50,000 USD" in results_a[0]["contentText"]

    # 2. Search for User B -> Should return ZERO results (Strict Tenant Isolation)
    results_b = await KnowledgeService.hybrid_vector_search(
        query="project budget deliverables",
        user_id=user_b.id,
        db=db_session
    )
    assert len(results_b) == 0

@pytest.mark.asyncio
async def test_rag_chat_with_citations_and_fallback(db_session: AsyncSession):
    user = UserModel(email="rag_tester@flowpilot.ai", password_hash=hash_password("Pass123!"), full_name="RAG Tester")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 1. Ask question when vault is empty -> returns no relevant docs fallback
    res_empty = await KnowledgeService.rag_chat_query("What is the refund policy?", user_id=user.id, db=db_session)
    assert res_empty["hasRelevantDocs"] == False
    assert len(res_empty["citations"]) == 0

    # 2. Upload document and ask relevant question -> returns answer + valid citations
    await KnowledgeService.process_document_upload(
        user_id=user.id,
        file_name="refund_policy.md",
        file_bytes=b"# Refund Policy\nAll freelance clients are eligible for full refund within 14 business days.",
        file_type="text/markdown",
        db=db_session
    )

    res_found = await KnowledgeService.rag_chat_query("What is the refund policy window?", user_id=user.id, db=db_session)
    assert res_found["hasRelevantDocs"] == True
    assert len(res_found["citations"]) == 1
    assert res_found["citations"][0]["documentTitle"] == "refund_policy.md"
