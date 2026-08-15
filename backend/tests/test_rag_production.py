import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_document_ingestion_and_rag_query_flow(async_client: AsyncClient):
    """1. Test PDF/Doc upload, text extraction, chunking, NVIDIA embeddings, and Nemotron 3 Ultra synthesis."""
    # 1. Register User A & Login
    await async_client.post("/api/v1/auth/register", json={"email": "rag_user_a@flowpilot.ai", "password": "Password123!", "fullName": "RAG User A"})
    login_a = await async_client.post("/api/v1/auth/login", json={"email": "rag_user_a@flowpilot.ai", "password": "Password123!"})
    token_a = login_a.cookies["flowpilot_session"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Upload Document
    doc_content = (
        "FlowPilot AI Architecture Overview:\n"
        "FlowPilot AI is an autonomous freelancing operating system powered by 10 specialized AI agents. "
        "The RAG Knowledge Vault enables high-accuracy document retrieval using NVIDIA Embeddings and Nemotron 3 Ultra model synthesis. "
        "Key features include lead CRM qualification, automated follow-ups, time management focus blocks, and MCP tool execution."
    )
    files = {"file": ("FlowPilot_Architecture_Doc.txt", doc_content.encode("utf-8"), "text/plain")}

    upload_res = await async_client.post("/api/v1/knowledge/upload", files=files, headers=headers_a)
    assert upload_res.status_code == 200
    doc_data = upload_res.json()
    assert doc_data["title"] == "FlowPilot_Architecture_Doc.txt"
    assert doc_data["chunkCount"] > 0
    doc_id_a = doc_data["id"]

    # 3. Query RAG Vault (Hybrid Search → Re-ranking → Nemotron 3 Ultra → Answer + Citations)
    query_res = await async_client.post(
        "/api/v1/knowledge/query",
        json={"query": "What is the RAG Knowledge Vault in FlowPilot AI?"},
        headers=headers_a
    )
    assert query_res.status_code == 200
    query_data = query_res.json()
    assert "answer" in query_data
    assert "citations" in query_data
    assert len(query_data["citations"]) > 0
    assert query_data["citations"][0]["documentTitle"] == "FlowPilot_Architecture_Doc.txt"


@pytest.mark.asyncio
async def test_rag_tenant_data_isolation(async_client: AsyncClient):
    """2. Verify User B cannot search, query, view, or retrieve User A's uploaded document chunks."""
    # 1. User A Register & Upload Document
    await async_client.post("/api/v1/auth/register", json={"email": "rag_owner_a@flowpilot.ai", "password": "Password123!", "fullName": "RAG Owner A"})
    login_a = await async_client.post("/api/v1/auth/login", json={"email": "rag_owner_a@flowpilot.ai", "password": "Password123!"})
    token_a = login_a.cookies["flowpilot_session"]

    files_a = {"file": ("UserA_Secret_Strategy.txt", b"User A Confidential Strategy: Project Codename Alpha has a budget of $250,000.", "text/plain")}
    res_a = await async_client.post("/api/v1/knowledge/upload", files=files_a, headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    doc_a_id = res_a.json()["id"]

    # 2. User B Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "rag_attacker_b@flowpilot.ai", "password": "Password123!", "fullName": "RAG Attacker B"})
    login_b = await async_client.post("/api/v1/auth/login", json={"email": "rag_attacker_b@flowpilot.ai", "password": "Password123!"})
    token_b = login_b.cookies["flowpilot_session"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User B attempts RAG query about User A's document
    b_query = await async_client.post(
        "/api/v1/knowledge/query",
        json={"query": "What is the budget for Project Codename Alpha?"},
        headers=headers_b
    )
    assert b_query.status_code == 200
    b_data = b_query.json()
    assert len(b_data["citations"]) == 0
    assert "$250,000" not in b_data["answer"]

    # 4. User B attempts direct document detail access -> 404
    b_doc_get = await async_client.get(f"/api/v1/knowledge/documents/{doc_a_id}", headers=headers_b)
    assert b_doc_get.status_code == 404

    # 5. User B attempts document deletion -> 404
    b_doc_del = await async_client.delete(f"/api/v1/knowledge/documents/{doc_a_id}", headers=headers_b)
    assert b_doc_del.status_code == 404
