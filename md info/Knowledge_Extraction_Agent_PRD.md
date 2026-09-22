# AGENT INFO GUIDE · Knowledge Extraction Agent (KEA)

---

## 1. Overview & Purpose

The **Knowledge Extraction Agent (KEA)** serves as the ingestion gateway for EduGra. It processes raw educational materials (specifically PDFs initially) and converts unstructured text into a structured, semantic knowledge graph stored in **Neo4j**.

Every downstream agent (Diagnostic, Planning, Student Modeling, Tutor) depends directly on the DAG (Directed Acyclic Graph) constructed by KEA.

---

## 2. Technical Stack & Architecture

- **Web Framework:** FastAPI (with Uvicorn)
- **PDF Extraction:** PyMuPDF (`fitz`)
- **LLM Routing:** LiteLLM (for model-agnostic completions and embeddings)
- **Database:** Neo4j (managed via the official `neo4j` Python driver)
- **Environment:** `python-dotenv` for managing credentials and API keys.

*Note: The choice of specific LLM models (e.g., `gemini-2.5-flash` for text extraction, `BAAI/bge-small-en-v1.5` for embeddings) is dictated by the `.env` configuration, abstracted via LiteLLM.*

---

## 3. End-to-End Pipeline Architecture (A to Z)

```
Upload File (POST /upload)
         │
         ▼
[ PDF Extractor ] ──▶ Extract Raw Text (PyMuPDF)
         │
         ▼
[ LLM Extraction ] ──▶ LiteLLM (via configured KNOWLEDGE_EXTRACTION_MODEL) ──▶ JSON Concept Schema
         │
         ▼
[ Vector Embedding ] ──▶ LiteLLM (via configured EMBEDDING_MODEL) ──▶ Float Vectors
         │
         ▼
[ Neo4j Graph Persistence ] ──▶ Cypher MERGE ──▶ Knowledge Graph DAG
```

---

## 4. Detailed Component Specifications

### 4.1 Folder Structure
```
app/
├── agents/
│   └── knowledge_extraction/
│       ├── __init__.py
│       ├── extractor.py       # PyMuPDF text extraction logic
│       ├── llm_extract.py     # LiteLLM concept extraction prompt & parsing
│       └── embeddings.py      # LiteLLM embedding generation
├── graph/
│   ├── __init__.py
│   ├── connection.py          # Neo4j driver singleton
│   └── graph_writer.py        # Cypher MERGE queries for concepts & relationships
├── models/
│   └── __init__.py
├── routes/
│   ├── __init__.py
│   └── upload.py              # FastAPI POST /upload endpoint
├── state/
│   └── __init__.py
└── main.py                    # FastAPI application entry point
scripts/
└── init_schema.py             # Script to initialize Neo4j constraints
tests/
└── fixtures/                  # Sample PDFs for standalone testing
```

### 4.2 Ingestion Layer (`app/agents/knowledge_extraction/extractor.py`)
* Uses `fitz` (PyMuPDF) to extract text page-by-page.
* Extracts the raw string to be passed into the LLM context.

### 4.3 LLM Extraction Engine (`app/agents/knowledge_extraction/llm_extract.py`)
* **Prompt Strategy:** Enforces strict JSON-only output without markdown wrappers or preambles.
* **Output Format:**
  ```json
  {
    "concepts": [
      {"name": "concept name", "definition": "one sentence definition", "prerequisites": ["concept name"]}
    ]
  }
  ```

### 4.4 Vector Embedding (`app/agents/knowledge_extraction/embeddings.py`)
* Iterates through the extracted concept names and calls LiteLLM's `embedding()` function.
* Returns a dictionary mapping concept names to their respective vector arrays.

### 4.5 Database Storage & Graph Schema (`Neo4j`)
* **Constraints (via `scripts/init_schema.py`):**
  - `CREATE CONSTRAINT concept_name_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE`
  - `CREATE CONSTRAINT student_id_unique IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE`
* **Concept Nodes & Prerequisite Edges (`app/graph/graph_writer.py`):**
  - Uses `MERGE` on Concept names to prevent duplicates and updates properties (`definition`, `embedding`, `subject`, `created_at`).
  - Uses `MERGE` to create `PREREQUISITE_OF` directional edges between prerequisite concepts and target concepts.

---

## 5. Input / Output Data Contracts

* **Input:** Raw File Byte Stream (via `POST /upload`).
* **Output:** JSON Response indicating status and number of concepts written.
  ```json
  {
    "status": "ok", 
    "concepts_written": 15
  }
  ```
