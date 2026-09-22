# AGENT INFO GUIDE · Planning Agent (PA)

---

## 1. Overview & Purpose

The **Planning Agent (PA)** generates an optimal, cognitively efficient learning sequence from a student's current knowledge state to their target learning goal. It takes the diagnosed `root_cause` from the Diagnostic Agent, extracts the sub-graph of weak prerequisites leading to `target_concept`, and sorts them using a topological DAG algorithm.

---

## 2. Unspecified Gaps ("Holes") in Initial Plan & Technical Resolutions

| Initial Plan Gap | Resolution & Actual Implementation Details |
|---|---|
| **Target Concept Ambiguity** | Initial plan assumed `target_concept` was always explicitly passed. Implemented an **Inference Engine** that matches words in `student_message` against concept names stored in Neo4j, falling back to `failed_concept` or default `"Integration"`. |
| **Pathfinding Algorithm Choice** | Initial plan referenced generic MSMS optimization without detailing execution logic. Implemented **Kahn's Algorithm for Topological Sorting** on the weak prerequisite DAG. |
| **Deterministic Ordering** | Pure queue-based topological sorts can produce non-deterministic paths. Implemented lexicographical queue sorting (`queue.sort()`) to guarantee deterministic path outputs across identical state inputs. |
| **Terminal Position Guarantee** | Topological sorts can accidentally place the target concept earlier if other nodes depend on it. Added an explicit post-processing step to re-anchor `target_concept` as the final node in `learning_path`. |

---

## 3. End-to-End Planning Pipeline (A to Z)

```
State Received: { root_cause, target_concept, student_message, mastery_threshold: 0.5 }
                                     │
                                     ▼
                [ Target Concept Set? ]
                    ├── NO  ──▶ Scan student_message vs Neo4j concept names
                    └── YES ──▶ Proceed with target_concept
                                     │
                                     ▼
                  [ Fetch Ancestor Sub-graph from Neo4j ]
                  MATCH (c:Concept)-[:PREREQUISITE_OF*0..10]->(t)
                                     │
                                     ▼
                   [ Filter Weak Nodes ("Sinks") ]
                   sinks = [c for c, score in sub_graph if score < 0.5]
                                     │
                                     ▼
            [ Execute Kahn's Topological Sorting Algorithm ]
            - Compute in-degrees for prerequisite edges between sinks
            - Process zero in-degree nodes via lexicographically sorted queue
                                     │
                                     ▼
                 [ Post-Processing & Target Anchoring ]
                 Ensure target_concept is placed at the end of learning_path
                                     │
                                     ▼
                        Return Planning Dictionary
```

---

## 4. Input / Output Data Contracts

* **Input State Keys (`StudentState`):**
  * `root_cause` (`str | None`): Identified root cause concept name.
  * `target_concept` (`str | None`): Desired learning goal concept.
  * `student_message` (`str`): Raw prompt text from user used for inference.
  * `mastery_threshold` (`float`, default `0.5`): Mastery score cutoff for filtering weak concepts.

* **Output State Keys Returned (`dict`):**
  * `target_concept` (`str`): Final resolved target concept name.
  * `learning_path` (`list[str]`): Sequenced array of concepts (e.g. `["Algebra", "Chain Rule", "Integration"]`).
  * `path_rationale` (`str`): Human-readable explanation of why this path was chosen.
  * `estimated_concepts` (`int`): Count of weak concepts in the generated sequence.

---

## 5. Implementation Reference Code File

* Code Implementation: [`planning.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/planning.py)
