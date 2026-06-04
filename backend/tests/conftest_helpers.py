"""Reusable HTTP helpers for tests (imported by test modules)."""
from __future__ import annotations

STRONG_JOB = {
    "company": "Acme AI",
    "role_title": "Applied AI Engineer",
    "description": "Build RAG systems and agent workflows.",
    "stack": ["Python", "FastAPI", "RAG", "LangGraph"],
    "requirements": "Python, FastAPI, RAG, LangGraph, APIs, automation.",
    "modality": "remote",
    "country": "Remote",
    "salary": 6000,
}

WEAK_JOB = {
    "company": "Old Corp",
    "role_title": "COBOL Mainframe Specialist",
    "description": "Maintain legacy mainframe batch jobs.",
    "stack": ["COBOL", "JCL", "DB2"],
    "requirements": "COBOL, JCL, DB2, mainframe operations on-site.",
    "modality": "onsite",
    "country": "Germany",
    "salary": 2000,
}


async def setup_strong_profile(client, headers) -> None:
    await client.put(
        "/api/v1/profile",
        headers=headers,
        json={"seniority": "mid", "preferred_modality": "remote", "salary_expectation": 5000},
    )
    for name in ["Python", "FastAPI", "RAG", "LangGraph"]:
        await client.post("/api/v1/profile/skills", headers=headers, json={"name": name})
    await client.post(
        "/api/v1/profile/projects",
        headers=headers,
        json={
            "title": "AgentDesk AI",
            "description": "Human-in-the-loop AI SupportOps with LangGraph and RAG.",
            "tech": ["FastAPI", "LangGraph", "RAG"],
        },
    )


async def create_job(client, headers, payload) -> str:
    resp = await client.post("/api/v1/jobs", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
