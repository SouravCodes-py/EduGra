# AGENT INFO GUIDE · Student Modeling Agent (SMA)

---

## 1. Overview & Purpose

The **Student Modeling Agent (SMA)** maintains a live, continuous numerical picture ($0.0$ to $1.0$) of a student's knowledge across every concept in the graph. It updates concept mastery scores stored directly on Neo4j `Concept` nodes after quiz attempts or tutoring interactions using a **Weighted Moving Average** algorithm.

Unlike conversational agents, SMA contains no LLM calls — it is built entirely on deterministic numerical calculations and database reads/writes.

---

## 2. Unspecified Gaps ("Holes") in Initial Plan & Technical Resolutions

| Initial Plan Gap | Resolution & Actual Implementation Details |
|---|---|
| **Graph Schema Property Storage** | Stored `mastery_score` property directly on `(c:Concept)` nodes in Neo4j (`c.mastery_score`), simplifying reads and writes. |
| **Dual-Mode Graph Execution Pattern** | Engineered two operating modes: **Mode 1 (UPDATE)** triggers when `interaction_score` is provided; **Mode 2 (READ-ONLY)** triggers on turn entry to read all concept scores. |
| **Score Update Formula Parameters** | Defined exact weighted moving average weights: $\text{Weight}_{\text{new}} = 0.3$, $\text{Weight}_{\text{old}} = 0.7$. |
| **Unseen Concept Default** | Set initial default mastery for unassessed concepts to `0.2` (assuming basic prior exposure). |
| **Boundary Clamping** | Score outputs are strictly clamped to $[0.0, 1.0]$ bounds before database persistence. |

---

## 3. Mathematical Formula & Operation Modes (A to Z)

### Weighted Moving Average Formula
$$\text{Mastery}_{\text{new}} = \max\Big(0.0, \, \min\big(1.0, \, (0.3 \times \text{Score}_{\text{interaction}}) + (0.7 \times \text{Mastery}_{\text{old}})\big)\Big)$$

### Dual Mode Flow
```
Mode Check: Is interaction_score present?
                 │
  ┌──────────────┴──────────────┐
  ▼                             ▼
[ Mode 1: UPDATE ]          [ Mode 2: READ-ONLY ]
- Read old score            - Query all (c:Concept)
- Apply formula               RETURN name, score
- Write new score to Neo4j  - Populate StudentState.mastery_scores
- Compute score_delta
```

---

## 4. Input / Output Data Contracts

* **Input State Keys (`StudentState`):**
  * `interaction_score` (`float | None`): Score between `0.0` and `1.0` from a quiz answer.
  * `current_concept` (`str | None`): Concept name being assessed.

* **Output State Keys Returned (`dict`):**
  * `mastery_scores` (`dict[str, float]`): Dictionary mapping concept names to mastery floats (`{"Chain Rule": 0.34, "Limits": 0.82}`).
  * `interaction_score` (`None`): Reset to `None` to prevent re-updating on subsequent pipeline iterations.
  * `score_delta` (`float | None`): Signed change in score (e.g. `+0.12`).

---

## 5. Implementation Reference Code File

* Code Implementation: [`student_modeling.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/student_modeling.py)
