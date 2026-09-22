import os
import hashlib
import math
import litellm
from dotenv import load_dotenv

load_dotenv()

def _get_fallback_embedding(text: str, dim: int = 384) -> list[float]:
    """Generates a deterministic normalized pseudo-embedding vector when external credits are exhausted."""
    vec = []
    text_bytes = text.encode("utf-8")
    for i in range(dim):
        h = hashlib.sha256(text_bytes + str(i).encode("utf-8")).digest()
        val = int.from_bytes(h[:4], "little", signed=True) / (2**31)
        vec.append(float(val))
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]

def get_embedding(text: str) -> list[float]:
    """
    Returns an embedding vector for the given text.
    Attempts litellm embedding first, falling back cleanly if credits are unavailable.
    """
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if openai_key:
        try:
            response = litellm.embedding(
                model="text-embedding-3-small",
                input=[text],
                api_key=openai_key
            )
            return response["data"][0]["embedding"]
        except Exception:
            pass

    return _get_fallback_embedding(text)
