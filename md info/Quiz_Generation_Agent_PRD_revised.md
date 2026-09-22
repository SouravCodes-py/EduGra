# AGENT INFO GUIDE · Quiz Generation Agent (QGA)

---

## 1. Overview & Purpose

The **Quiz Generation Agent (QGA)** generates personalized, difficulty-calibrated assessment questions for the concept currently being taught. It separates assessment from instruction (Tutor Agent). When the Tutor Agent determines that a concept needs assessment (`quiz_triggered = True`), control routes to QGA to produce question sets.

---

## 2. Unspecified Gaps ("Holes") in Initial Plan & Technical Resolutions

| Initial Plan Gap | Resolution & Actual Implementation Details |
|---|---|
| **Pipeline Integration Contract** | Initial plan did not specify how quiz outputs reached the frontend. Engineered a dedicated response structure in `StudentState` (`quiz_questions`) consumed by FastAPI `POST /chat` and submitted back via `POST /quiz/answer`. |
| **Question Structure Standard** | Standardized quiz question objects with three essential attributes: `type` (`"recall"`, `"application"`, `"conceptual"`), `question_text`, and `difficulty` (`"easy"`, `"medium"`, `"hard"`). |
| **Current Development State** | Implemented as a deterministic Python stub module (`quiz_generation.py`) to unblock end-to-end graph state execution before full LLM question generation wiring. |

---

## 3. Data Contracts & Data Structures (A to Z)

```
Triggered by Tutor Agent (quiz_triggered = True)
                       │
                       ▼
          [ Execute run_quiz_generation ]
                       │
                       ▼
Generate Structured Quiz Question Array
                       │
                       ▼
Return { quiz_questions: [...] } in StudentState
                       │
                       ▼
Frontend Renders Quiz -> User Answers -> POST /quiz/answer -> Student Modeling Update
```

### Question Object Schema
```python
{
    "quiz_questions": [
        {
            "type": "recall",
            "question_text": "What is the chain rule?",
            "difficulty": "easy"
        },
        {
            "type": "application",
            "question_text": "If f(x) = sin(x²), what is f′(x)?",
            "difficulty": "medium"
        },
        {
            "type": "conceptual",
            "question_text": "Why does the chain rule require multiplying outer and inner derivatives?",
            "difficulty": "hard"
        }
    ]
}
```

---

## 4. API Endpoints

* **`POST /chat`**: Includes `quiz` payload when `quiz_triggered = True`.
* **`POST /quiz/answer`**: Accepts student answer selection (`session_id`, `concept`, `question_id`, `selected_index`), passes numerical score to `Student Modeling Agent`, and returns updated concept mastery.

---

## 5. Implementation Reference Code File

* Code Implementation: [`quiz_generation.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/quiz_generation.py)
