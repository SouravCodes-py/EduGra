# GraphMASAL System & Pipeline Technical Guide

This document provides a master technical guide for the entire **GraphMASAL** multi-agent learning system, detailing how all 7 agents, databases, and AI models work together from end to end (A to Z).

---

## 1. System Pipeline Architecture

```
                                [ Upload Document ]
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Pipeline A: Knowledge Extraction Pipeline                                        │
│ Code: backend/agents/knowledge_extraction/extraction_agent.py                  │
│ Models: Google Gemini 2.5 Flash + gemini-embedding-001                         │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Populates Concept DAG
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Pipeline B: Stateful Adaptive Tutor Pipeline (LangGraph DAG)                   │
│ Code: pipeline/graph.py & pipeline/agents/                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Unspecified Gaps ("Holes") Found & Resolved Across Pipelines

Below is the complete list of architectural gaps that were not specified in initial plans and how they were designed, implemented, and resolved in the codebase:

1. **Multi-format Document Ingestion (KEA):**
   * *Gap:* Plan did not detail how varied input formats were parsed.
   * *Resolution:* Built a modular loader factory (`loader_factory.py`) with specialized parsers (`pdf_loader.py` via PyMuPDF, `docx_loader.py`, `pptx_loader.py`, `txt_loader.py`, `markdown_loader.py`).

2. **Decoupled 3-Step Extraction (KEA):**
   * *Gap:* Extracting concepts, definitions, embeddings, and prerequisites in a single LLM prompt caused context overflow and invalid JSON output.
   * *Resolution:* Decoupled into Step 1 (Gemini 2.5 Flash concept extraction), Step 2 (Gemini `models/gemini-embedding-001` batched vector generation), and Step 3 (Gemini 2.5 Flash prerequisite relationship extraction).

3. **Mastery Property Placement on Neo4j Graph (DA / SMA):**
   * *Gap:* Initial PRDs referenced storing mastery scores on separate `HAS_MASTERY` edges.
   * *Resolution:* Consolidated schema to store `mastery_score` directly as a float property on `Concept` nodes (`c.mastery_score`), speeding up Cypher traversal performance.

4. **Multi-Criteria Diagnostic Sorting (DA):**
   * *Gap:* Plan lacked specific ordering rules for selecting among multiple weak prerequisite ancestors.
   * *Resolution:* Built Cypher query `ORDER BY depth DESC, root.mastery_score ASC LIMIT 1` to prioritize the deepest ancestor node, and among equal-depth nodes, the weakest score.

5. **Topological Learning Path Planning (PA):**
   * *Gap:* Plan referenced generic MSMS optimization without detailing execution logic.
   * *Resolution:* Implemented **Kahn's Algorithm for Topological Sorting** on the weak prerequisite DAG, with lexicographical queue sorting to guarantee deterministic path outputs and a terminal placement check for `target_concept`.

6. **Dual-Mode Student Modeling Execution (SMA):**
   * *Gap:* Plan did not detail how numerical tracking integrated with state machine execution turns.
   * *Resolution:* Created **Mode 1 (UPDATE)** using a Weighted Moving Average ($0.3 \times \text{new} + 0.7 \times \text{old}$) when an `interaction_score` is present, and **Mode 2 (READ-ONLY)** on every turn start to pull current mastery states.

7. **Multi-Context Tutor Synthesizer & LiteLLM Integration (TA):**
   * *Gap:* Plan did not specify how inputs from 5+ agents were combined into a prompt.
   * *Resolution:* Built a unified system prompt synthesizer taking student tone, diagnosed root cause, active topological study path, current focus concept, mastery scores map, and retrieved top-3 memories, executing via **LiteLLM** (`claude-sonnet-4-20250514` default).

8. **Dual-Model Semantic Vector Memory (MA):**
   * *Gap:* Plan was ambiguous on memory generation and vector search execution.
   * *Resolution:* Paired **Groq (`llama-3.3-70b-versatile`)** for fast 2-3 sentence session summarization with **Google Embeddings** (`models/gemini-embedding-001`) and **Supabase `pgvector`** for cosine similarity search (`match_semantic_memories`).

---

## 3. Master Agent Mapping Table

| Agent | Info Guide PRD | Status | Implementation File | Key Models & Tech Stack |
|---|---|---|---|---|
| **Knowledge Extraction (KEA)** | [`Knowledge_Extraction_Agent_PRD.md`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/Agents/Knowledge_Extraction_Agent_PRD.md) | **Implemented** | [`extraction_agent.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/backend/agents/knowledge_extraction/extraction_agent.py) | Gemini 2.5 Flash, `gemini-embedding-001`, PyMuPDF, Neo4j |
| **Diagnostic (DA)** | [`Diagnostic_Agent_PRD.md`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/Agents/Diagnostic_Agent_PRD.md) | **Implemented** | [`diagnostic.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/diagnostic.py) | Neo4j 10-hop Cypher Traversal |
| **Planning (PA)** | [`Planning_Agent_PRD.md`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/Agents/Planning_Agent_PRD.md) | **Implemented** | [`planning.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/planning.py) | Kahn's Topological Sort Algorithm |
| **Student Modeling (SMA)** | [`Student_Modeling_Agent_PRD.md`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/Agents/Student_Modeling_Agent_PRD.md) | **Implemented** | [`student_modeling.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/student_modeling.py) | Weighted Moving Average, Neo4j |
| **Tutor (TA)** | [`Tutor_Agent_PRD_revised.md`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/Agents/Tutor_Agent_PRD_revised.md) | **Implemented** | [`tutor.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/tutor.py) | LiteLLM (`claude-sonnet-4-20250514`) |
| **Memory (MA)** | [`Memory_Agent_PRD_revised.md`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/Agents/Memory_Agent_PRD_revised.md) | **Implemented** | [`memory_agent.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/backend/agents/memory/memory_agent.py) | Groq Llama 3.3 70B, Google Embedding, Supabase pgvector |
| **Quiz Generation (QGA)** | [`Quiz_Generation_Agent_PRD_revised.md`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/Agents/Quiz_Generation_Agent_PRD_revised.md) | **Implemented (Stub Mode)** | [`quiz_generation.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/quiz_generation.py) | Python stub module |
