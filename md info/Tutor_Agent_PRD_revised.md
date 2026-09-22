# AGENT INFO GUIDE · Tutor Agent (TA)

---

## 1. Overview & Purpose

The **Tutor Agent (TA)** acts as the primary conversational interface for GraphMASAL. It synthesizes structured outputs from all upstream agents (diagnosed root causes, active learning paths, student mastery scores, and retrieved long-term memories) into natural, personalized, pedagogically sound conversational dialogue.

---

## 2. Unspecified Gaps ("Holes") in Initial Plan & Technical Resolutions

| Initial Plan Gap | Resolution & Actual Implementation Details |
|---|---|
| **Multi-Agent Context Integration** | Initial plan did not specify how inputs from 5+ agents were combined into an LLM prompt. Engineered a **Structured System Prompt Synthesizer** unifying student profile, active study path, diagnosed root cause, mastery scores, and memory summaries. |
| **Model Provider Flexibility** | Integrated **LiteLLM** to decouple agent code from a single LLM vendor, allowing seamless switching across Anthropic (`claude-sonnet-4-20250514`), OpenAI (`gpt-4o`), Google Gemini, and Groq. |
| **API Key Missing / Offline Fallback** | Implemented environment key validation (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`). If keys are missing or API calls fail, TA returns domain-aware fallback text to prevent pipeline crashes. |
| **Automated Quiz Dispatch Logic** | Added dynamic assessment checking: if `mastery_scores[current_concept] < 0.5`, TA automatically sets `quiz_triggered = True`, routing execution to the Quiz Generation Agent. |

---

## 3. System Prompt Construction & Execution (A to Z)

```
Inputs: { student_id, student_message, tone_preference, learning_path, root_cause, mastery_scores, memory_context }
                                            │
                                            ▼
                       [ Synthesize Contextual System Prompt ]
                       - Add Student Profile & Tone Instructions
                       - Add Diagnosed Root Cause & Active Study Path
                       - Format Mastery Scores & Top-3 Past Memories
                                            │
                                            ▼
                       [ Execute LLM Call via LiteLLM ]
                       Model: LITELLM_MODEL_TUTOR (default: claude-sonnet-4-20250514)
                                            │
                                            ▼
                 [ Evaluate Mastery Score for Quiz Trigger ]
                 Is current_concept mastery < 0.5? ──▶ Set quiz_triggered
                                            │
                                            ▼
                               Return Tutor Response Dict
```

---

## 4. Input / Output Data Contracts

* **Input State Keys (`StudentState`):**
  * `student_id` (`str`): Unique identifier for student.
  * `student_message` (`str`): User input query.
  * `tone_preference` (`str`, default `"encouraging"`): Tone style choice.
  * `learning_path` (`list[str]`): Sequenced array of concepts.
  * `root_cause` (`str | None`): Diagnosed root-cause weakness.
  * `mastery_scores` (`dict[str, float]`): Current concept scores.
  * `memory_context` (`list[str]`): Retrieved past session summaries.

* **Output State Keys Returned (`dict`):**
  * `tutor_response` (`str`): Conversational output message.
  * `quiz_triggered` (`bool`): Flag indicating if quiz assessment should run next.
  * `current_concept` (`str | None`): Current active concept being addressed.
  * `new_concept_flagged` (`bool`): Flag indicating if student introduced an un-modeled concept.

---

## 5. Implementation Reference Code File

* Code Implementation: [`tutor.py`](file:///c:/A%20ME%20STUFF/STUDIES/EXTRA/ML/SUMMER%20PROJECT%202026/graphmasal/pipeline/agents/tutor.py)
