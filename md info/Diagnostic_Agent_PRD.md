# AGENT INFO GUIDE · Diagnostic Agent (DA)

---

## 1. Overview & Purpose

The **Diagnostic Agent (DA)** performs root-cause analysis when a student struggles with a concept. Rather than assuming the surface-level failed concept is the sole problem, DA traces backward through the prerequisite graph in Neo4j up to 10 hops to identify the deepest, weakest foundational prerequisite causing the failure.

---

## 2. Unspecified Gaps ("Holes") in Initial Plan & Technical Resolutions

| Initial Plan Gap | Resolution & Actual Implementation Details |
|---|---|
| **Graph Schema Misalignment** | Initial PRD specified storing mastery scores on a separate `HAS_MASTERY` relationship. The production schema stores `mastery_score` directly on the `Concept` node (`c.mastery_score`), streamlining Cypher execution. |
| **Root Cause Sorting Criteria** | Ambiguity existed on how to pick between multiple weak ancestors. Resolved by implementing a dual-sort Cypher query: `ORDER BY depth DESC, root.mastery_score ASC LIMIT 1` (selects the furthest-back weak node first, and among ties, the weakest score). |
| **Cycle & Infinite Loop Defense** | Prerequisite graphs can contain accidental cycles. Implemented explicit variable-length path bounds (`*1..10`). |
| **Graceful Degraded Execution** | If no weak prerequisites exist, or if the concept is missing from the database, DA sets `root_cause = failed_concept` at `diagnosis_depth = 0` to prevent pipeline stalls. |

---

## 3. Execution Pipeline & Cypher Query Logic (A to Z)

```
State Received: { failed_concept, mastery_threshold: 0.5 }
                           │
                           ▼
              [ Is failed_concept present? ]
                  ├── NO  ──▶ Return empty diagnosis (root_cause: None)
                  └── YES ──▶ Run 10-hop Cypher Traversal in Neo4j
                                       │
                                       ▼
                     [ Weak Prerequisites Found? ]
                         ├── YES ──▶ Select Deepest Weak Ancestor (root_cause, root_mastery, depth)
                         └── NO  ──▶ Return direct failed_concept (depth: 0)
                                       │
                                       ▼
                   Write outputs to StudentState & return
```

### The Production Cypher Query
```cypher
MATCH path = (root:Concept)-[:PREREQUISITE_OF*1..10]->(failed:Concept {name: $failed_concept})
WHERE root.mastery_score < $mastery_threshold
RETURN root.name AS root_cause,
       root.mastery_score AS root_mastery,
       length(path) AS depth
ORDER BY depth DESC, root.mastery_score ASC
LIMIT 1
```

---

## 4. Input / Output Data Contracts

* **Input State Keys (`StudentState`):**
  * `failed_concept` (`str | None`): Surface concept student failed (e.g. `"Integration"`).
  * `mastery_threshold` (`float`, default `0.5`): Mastery score boundary for defining weakness.

* **Output State Keys Returned (`dict`):**
  * `root_cause` (`str | None`): Identified root cause concept name (e.g. `"Chain Rule"`).
  * `root_mastery` (`float | None`): Numerical score of the root cause concept (e.g. `0.34`).
  * `diagnosis_depth` (`int | None`): Number of graph hops back from the failed concept (e.g. `2`).

---

## 5. Edge Case & Fallback Rules

1. **First Turn / No Failure:** If `failed_concept` is `None`, DA logs an informational message and returns `{ root_cause: None, root_mastery: None, diagnosis_depth: None }`.
2. **All Prerequisites Strong:** If all ancestors have `mastery_score >= threshold`, DA queries the mastery of `failed_concept` itself and sets it as the `root_cause` at `depth = 0`.
3. **Database Error:** Wrapped in a global `try-except` block to ensure runtime errors log detailed tracebacks while returning a fallback dict, ensuring LangGraph never crashes.

---

## 6. Implementation Reference Code File

* Code Implementation: [`diagnostic.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/diagnostic.py)
