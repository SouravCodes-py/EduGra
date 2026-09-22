import litellm
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

PROMPT = """You are extracting a knowledge graph from study material.
Return ONLY valid JSON. No preamble, no markdown.

Format:
{{
  "concepts": [
    {{"name": "concept name", "definition": "one sentence definition", "prerequisites": ["concept name"]}}
  ]
}}

Rules:
- Prerequisites must also appear in the concepts list or be foundational topics
- Definitions must be self-contained — no references to other concepts
- Only include concepts explicitly taught in the material

Material:
{text}
"""

def extract_concepts(text: str) -> dict:
    # Truncate text if needed to fit context comfortably
    max_chars = 12000
    cleaned_text = text[:max_chars] if len(text) > max_chars else text

    # Select model based on available environment variables
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if groq_key:
        model = "groq/openai/gpt-oss-120b"
        api_key = groq_key
    elif gemini_key:
        model = "gemini/gemini-2.5-flash"
        api_key = gemini_key
    else:
        model = "gpt-4o"
        api_key = os.getenv("LLM_API_KEY")

    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": PROMPT.format(text=cleaned_text)}],
        api_key=api_key,
        temperature=0.1,
    )
    
    raw = response.choices[0].message.content.strip()
    
    # Strip markdown code blocks if present
    if "```" in raw:
        match = re.search(r"```(?:json)?(.*?)```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
        else:
            raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
    except Exception:
        # Fallback regex search for JSON object with concepts
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            data = {"concepts": []}

    return data