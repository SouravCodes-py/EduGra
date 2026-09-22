# GraphMASAL — Comprehensive LLM & AI Model Guide

This guide details all LLM (Large Language Model), Embedding, and Algorithmic models used across GraphMASAL, their exact purpose, why each was chosen, how they are called in code, execution mode (Cloud vs. Local), and free-tier daily quotas.

---

## 1. Summary Matrix of AI Models

| Model Name | Type | Provider / Host | Execution | Agent / Component | Purpose | Free-Tier Quota & Daily Limit |
|---|---|---|---|---|---|---|
| **`llama-3.1-8b-instant`** | LLM | `groq` / LiteLLM | **Cloud** | Tutor Agent (TA) | High-frequency conversational tutoring turns | **14,400 Requests/Day** (30 RPM, 0 Cost) |
| **`llama-3.3-70b-versatile`** | LLM | `groq` / LiteLLM | **Cloud** | Quiz & Memory Agent (MA) | Quiz generation & session summarization | **1,000 Requests/Day** (30 RPM, 0 Cost) |
| **`gemini-2.5-flash`** | LLM | `google-generativeai` | **Cloud** | Knowledge Extraction Agent (KEA) | Concept & prerequisite JSON extraction from files | **250 Requests/Day** (10 RPM, Free Tier) |
| **`BAAI/bge-small-en-v1.5`** | Embedding | Local Python (`fastembed`) | **Local** | KEA & Memory Agent (MA) | 384-dim vector embeddings for concepts & memory search | **UNLIMITED** (0 API calls, 0 cost) |

---

## 2. In-Depth Breakdown by Agent & Task

### 2.1 Groq — Llama 3.1 8B Instant (`llama-3.1-8b-instant`) & Llama 3.3 70B (`llama-3.3-70b-versatile`)
* **Agent:** Tutor Agent ([`tutor.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/tutor.py)), Memory Agent, Quiz Generation Agent
* **Tasks:**
  1. **Tutor Dialogue:** Generates real-time, encouraging conversational explanations tailored to the active study path and student tone preferences.
  2. **Session Summarization:** Distills turn logs and attempt scores into 2–3 sentence factual summaries for vector memory.
  3. **Quiz Generation:** Generates difficulty-calibrated assessment questions (`easy`, `medium`, `hard`).
* **Why Chosen:** 
  * **Ultra-Fast Speed:** ~276 to 750+ tokens/second on Groq LPUs. Responses return in <0.3s.
  * **Academic Benchmarks:** Llama 3.3 70B scores **77.0% on MATH**, **91.1% on MGSM** (multilingual math), and **86.0% on MMLU**.
  * **High Daily Quotas:** Groq provides **14,400 requests/day** for Llama 3.1 8B Instant, completely solving daily quota bottlenecks for student chat.

---

### 2.2 Local Embeddings (`fastembed` / `BAAI/bge-small-en-v1.5`)
* **Agent:** Knowledge Extraction Agent & Memory Agent ([`memory_agent.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/backend/agents/memory/memory_agent.py))
* **Tasks:**
  1. **Concept Vectorization:** Converts extracted concepts into dense float vectors stored in Neo4j.
  2. **Memory Search:** Converts student session summaries into vector embeddings for cosine similarity search in Supabase (`pgvector`).
* **Why Chosen:** Runs 100% **locally** on CPU/GPU using Python's `fastembed` package. **Zero API calls, zero rate limits, zero daily cost.**

---

### 2.3 Google Gemini 2.5 Flash (`gemini-2.5-flash`)
* **Agent:** Knowledge Extraction Agent ([`extraction_agent.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/backend/agents/knowledge_extraction/extraction_agent.py))
* **Tasks:**
  * **Concept & Relationship Extraction:** Parses raw textbook documents (PDF, DOCX, TXT) into structured concept nodes and `PREREQUISITE_OF` dependency edges.
* **Why Chosen:** Exceptional structured JSON output reliability and 1M+ token context window for document ingestion. Used only for batch textbook processing (infrequent operation).

---

## 3. Execution Infrastructure & Security Guidance

### Cloud vs. Local Execution Summary
* **Cloud Infrastructure:** Groq and Google Gemini inference requests run on external cloud LPU/GPU clusters via secure HTTPS API calls.
* **Local Infrastructure:** Vector embeddings (`fastembed`) run 100% locally on the application host.
* **Scale & Capacity for 2–3 Users:** With 2–3 active users, Groq's 14,400 daily requests allow ~4,800 chat messages per user per day. Daily quotas will never be exhausted.
* **Deployment Security:** Always exclude `.env` from Git commits using `.gitignore` to prevent API key leakage. Store keys in secure environment variables on hosting platforms (e.g. Render/Vercel).

---

## 4. Non-LLM Algorithmic Engines (Deterministic Agents)

GraphMASAL employs deterministic graph algorithms and numerical logic for non-text tasks:

1. **Diagnostic Agent (DA):** Uses **Neo4j 10-hop Cypher Traversal** (`MATCH path = (root:Concept)-[:PREREQUISITE_OF*1..10]->(failed:Concept)`) to isolate root causes.
2. **Planning Agent (PA):** Uses **Kahn's Topological Sorting Algorithm** on the prerequisite DAG subset to generate optimal study paths.
3. **Student Modeling Agent (SMA):** Uses a **Weighted Moving Average** ($\text{Mastery}_{\text{new}} = 0.3 \times \text{Score} + 0.7 \times \text{Mastery}_{\text{old}}$) to update concept scores.

