# AGENT INFO GUIDE · Knowledge Extraction Agent (KEA)

---

## 1. Overview & Purpose

The **Knowledge Extraction Agent (KEA)** serves as the ingestion gateway for GraphMASAL. It processes raw educational materials (PDFs, Word documents, PowerPoint presentations, Markdown, and plain text files) and converts unstructured text into a structured, semantic knowledge graph stored in **Neo4j**.

Every downstream agent (Diagnostic, Planning, Student Modeling, Tutor) depends directly on the DAG (Directed Acyclic Graph) constructed by KEA.

---

## 2. Unspecified Gaps ("Holes") in Initial Plan & Technical Resolutions

| Initial Plan Gap | Resolution & Actual Implementation Details |
|---|---|
| **Multi-format Document Ingestion** | Implemented a modular loader factory (`loader_factory.py`) with specialized document parsers (`pdf_loader.py` via PyMuPDF, `docx_loader.py`, `pptx_loader.py`, `txt_loader.py`, `markdown_loader.py`). |
| **Single-pass LLM Failure** | Passing text to extract concepts, definitions, embeddings, and relationships in a single LLM prompt caused context overflow and hallucinated JSON. Resolved by engineering a **3-Step Decoupled Extraction Pipeline**. |
| **Malformed JSON & Markdown Wrappers** | LLMs wrap JSON responses in markdown fences (````json ... ````). Built a regex sanitizer (`_clean_json`) and Pydantic schemas (`models.py`) to enforce strict type validation. |
| **Vector Embedding Choice** | Selected Google `models/gemini-embedding-001` with `SEMANTIC_SIMILARITY` task type for batched concept vector generation. |
| **Graph Merging vs Duplication** | Implemented Cypher `MERGE` statements on concept names to ensure uploading new files updates existing nodes rather than creating duplicate concepts. |

---

## 3. End-to-End Pipeline Architecture (A to Z)

```
Upload File (POST /upload)
         │
         ▼
[ Loader Factory ] ──▶ Extract Raw Text (PyMuPDF / docx / pptx)
         │
         ▼
[ Step 1: Concept Extraction ] ──▶ Gemini 2.5 Flash ──▶ Pydantic ConceptList
         │
         ▼
[ Step 2: Batched Embedding ] ──▶ gemini-embedding-001 ──▶ 3072-dim Float Vectors
         │
         ▼
[ Step 3: Relationship Extraction ] ──▶ Gemini 2.5 Flash ──▶ PREREQUISITE_OF Edges
         │
         ▼
[ Step 4: Neo4j Graph Persistence ] ──▶ Cypher MERGE ──▶ Knowledge Graph DAG
```

---

## 4. Detailed Component Specifications

### 4.1 Ingestion Layer (`backend/ingestion/`)
* **`base_loader.py`**: Abstract base class defining `load(file_path: str) -> str`.
* **`pdf_loader.py`**: Uses `fitz` (PyMuPDF) to extract text page-by-page, stripping page numbers and header artifacts.
* **`docx_loader.py` / `pptx_loader.py`**: Parses paragraph blocks and slide shapes into ordered text strings.

### 4.2 LLM Extraction Engine (`backend/agents/knowledge_extraction/extraction_agent.py`)

#### Step 1 — Concept Extraction
* **Model:** `gemini-2.5-flash` (`temperature=0.2`, `max_output_tokens=4096`)
* **Prompt Strategy:** Enforces JSON-only output complying with Pydantic schema:
  ```json
  {
    "concepts": [
      {
        "id": "c1",
        "name": "Chain Rule",
        "description": "Rule for differentiating composite functions.",
        "prerequisites": ["Derivatives", "Functions"]
      }
    ]
  }
  ```

#### Step 2 — Batched Vector Embedding
* **Model:** `models/gemini-embedding-001`
* **Execution:** Collects all extracted concept names into a single list and calls `genai.embed_content()` in batch, assigning embedding vectors directly to `Concept.embedding`.

#### Step 3 — Prerequisite Relationship Extraction
* **Model:** `gemini-2.5-flash` (`temperature=0.2`)
* **Context Window:** Passes raw text alongside the list of extracted concept names and descriptions.
* **Output:** Extracts directed directional dependencies:
  ```json
  {
    "relationships": [
      {
        "source": "Chain Rule",
        "target": "Integration",
        "relationship_type": "PREREQUISITE_OF",
        "weight": 1.0
      }
    ]
  }
  ```

### 4.3 Database Storage & Graph Schema (`Neo4j`)
* **Concept Nodes:**
  ```cypher
  MERGE (c:Concept {name: $name})
  ON CREATE SET c.id = $id,
                c.description = $description,
                c.embedding = $embedding,
                c.mastery_score = 0.2,
                c.created_at = timestamp()
  ```
* **Prerequisite Edges:**
  ```cypher
  MATCH (a:Concept {name: $source})
  MATCH (b:Concept {name: $target})
  MERGE (a)-[r:PREREQUISITE_OF]->(b)
  SET r.weight = $weight
  ```

---

## 5. Input / Output Data Contracts

* **Input:** Raw File Byte Stream (via `POST /upload`).
* **Output:** Structured dictionary representation of `KnowledgeGraph`:
  ```python
  {
      "concepts": [
          {"id": str, "name": str, "description": str, "embedding": list[float]}
      ],
      "relationships": [
          {"source": str, "target": str, "relationship_type": "PREREQUISITE_OF", "weight": float}
      ]
  }
  ```

---

## 6. Implementation Reference Code Files

* Agent Class: [`extraction_agent.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/backend/agents/knowledge_extraction/extraction_agent.py)
* Data Models: [`models.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/backend/agents/knowledge_extraction/models.py)
* Prompts: [`prompts.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/backend/agents/knowledge_extraction/prompts.py)
* Ingestion Loaders: [`loader_factory.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/backend/ingestion/loader_factory.py)
