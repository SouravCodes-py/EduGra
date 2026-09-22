import litellm
import json
import os
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
- Prerequisites must also appear in the concepts list
- Definitions must be self-contained — no references to other concepts
- Only include concepts explicitly taught in the material

Material:
{text}
"""

def extract_concepts(text: str) -> dict:
    response = litellm.completion(
        model="gemini/gemini-3.6-flash",
        messages=[{"role": "user", "content": PROMPT.format(text=text)}],
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    raw = response.choices[0].message.content.strip()
    # Gemini sometimes wraps JSON in markdown fences despite instructions — strip if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())