# AGENT INFO GUIDE · Memory Agent (MA)

---

## 1. Overview & Purpose

The **Memory Agent (MA)** provides semantic long-term memory for GraphMASAL. It captures qualitative summaries of student tutoring sessions, converts them into dense vector embeddings, and stores them in **Supabase (pgvector)**. When a student starts a new session or asks a question, MA performs cosine similarity vector searches to retrieve the top-3 most relevant past memories.

---

## 2. Unspecified Gaps ("Holes") in Initial Plan & Technical Resolutions

| Initial Plan Gap | Resolution & Actual Implementation Details |
|---|---|
| **Multi-Model Pipeline Specification** | Initial plan was ambiguous about how semantic summaries were produced and vectorized. Resolved by pairing **Groq (`llama-3.3-70b-versatile`)** for fast 2-3 sentence summarization with **Google Embeddings** (`models/gemini-embedding-001` / `text-embedding-004`) for vector generation. |
| **Vector DB Setup & Cosine Search** | Integrated **Supabase `pgvector`** with a custom stored RPC function (`match_semantic_memories`) to filter records by `student_id` and rank by cosine similarity (`TOP_K = 3`). |
| **Session Event Synthesizer** | Structured `write_memory` in `pipeline/agents/memory.py` to extract turn events (concepts attempted, scores, struggle results, root causes) and pass them as JSON payload to Groq. |
| **Import Safety & Fault Tolerance** | Wrapped Supabase and Groq initializations in lazy client initializers (`_get_groq()`, `_get_supabase()`) with fallback dummy functions to protect pipeline execution if keys are missing. |

---

## 3. Operations: Write & Fetch Architecture (A to Z)

```
======================================================================================
WRITE FLOW: write(student_id, session_events)
======================================================================================
Session Events JSON Payload
         │
         ▼
[ Groq LLM: llama-3.3-70b-versatile ] ──▶ Generate 2-3 sentence factual summary
         │
         ▼
[ Google Embedding API ] ──────────────▶ Generate Float Vector Embedding
         │
         ▼
[ Supabase Insert ] ────────────────────▶ Persist to semantic_memories table
                                           (student_id, summary, embedding, created_at)

======================================================================================
FETCH FLOW: fetch(student_id, query)
======================================================================================
Natural Language Query String
         │
         ▼
[ Google Embedding API ] ──────────────▶ Generate Query Vector Embedding
         │
         ▼
[ Supabase RPC Call ] ─────────────────▶ match_semantic_memories(p_student_id, p_embedding, 3)
         │
         ▼
Return Top-3 Summary Strings ─────────▶ Inject into StudentState.memory_context
```

---

## 4. Input / Output Data Contracts

### 4.1 Write Routine (`write`)
* **Parameters:** `student_id: str`, `session_events: list[dict]`
* **Sample Event Item:** `{"concept": "Chain Rule", "score": 0.4, "result": "struggled"}`
* **Returns:** `str | None` (Generated summary string on success).

### 4.2 Fetch Routine (`fetch`)
* **Parameters:** `student_id: str`, `query: str`
* **Returns:** `list[str]` (Top-3 summary strings ordered by vector similarity).

---

## 5. Database Schema & RPC Stored Function

### Supabase Table (`semantic_memories`)
```sql
CREATE TABLE semantic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    embedding VECTOR(3072) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Supabase RPC Function (`match_semantic_memories`)
```sql
CREATE OR REPLACE FUNCTION match_semantic_memories(
    p_student_id TEXT,
    p_embedding VECTOR(3072),
    p_match_count INT
)
RETURNS TABLE (id UUID, summary TEXT, similarity FLOAT)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT m.id, m.summary, 1 - (m.embedding <=> p_embedding) AS similarity
    FROM semantic_memories m
    WHERE m.student_id = p_student_id
    ORDER BY m.embedding <=> p_embedding
    LIMIT p_match_count;
END;
$$;
```

---

## 6. Implementation Reference Code Files

* Core Memory Module: [`memory_agent.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/backend/agents/memory/memory_agent.py)
* LangGraph Integration: [`memory.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/memory.py)
