"""
Vision AI service — receipt scanning via Ollama or Gemini.
Extracts: amount, description (vendor), date from receipt images.
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any

# Try Ollama first, fallback to httpx for Gemini
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

import os

import httpx

OLLAMA_DEFAULT = "http://localhost:11434"


def _ollama_base_url() -> str:
    """Ollama URL: OLLAMA_BASE_URL env or localhost:11434 (WSL2 forwards to host)."""
    return os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT).rstrip("/")


PROMPT = """Extract the total amount, vendor/store name, and date from this receipt image.
Return ONLY valid JSON with these exact keys (no markdown, no extra text):
{"amount": <float>, "description": "<vendor/store name>", "date": "<YYYY-MM-DD or best guess>"}
If you cannot read something, use null for that field."""


def _parse_ai_response(text: str) -> dict[str, Any]:
    """Parse AI response into structured dict. Handles markdown code blocks."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract JSON object (handles nested braces)
    start = text.find("{")
    if start >= 0:
        depth = 0
        for i, c in enumerate(text[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
    raise ValueError("Could not parse JSON from AI response")


def _extract_content(response: Any) -> str:
    """Extract text from ollama response (dict or object)."""
    if isinstance(response, dict):
        return response.get("message", {}).get("content", "{}")
    msg = getattr(response, "message", None)
    return getattr(msg, "content", "{}") if msg else "{}"


def analyze_receipt_ollama(image_bytes: bytes, model: str = "llava:7b") -> dict[str, Any]:
    """Use Ollama vision model to analyze receipt."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    img_data = f"data:image/jpeg;base64,{b64}" if not b64.startswith("data:") else b64
    kwargs = {"model": model, "messages": [{"role": "user", "content": PROMPT, "images": [img_data]}]}
    if hasattr(ollama, "Client"):
        response = ollama.Client(host=_ollama_base_url()).chat(**kwargs)
    else:
        response = ollama.chat(**kwargs)
    content = _extract_content(response)
    return _parse_ai_response(content)


def analyze_receipt_via_api(
    image_bytes: bytes,
    base_url: str | None = None,
    model: str = "llava:7b",
) -> dict[str, Any]:
    """Use Ollama HTTP API directly (no ollama library)."""
    base_url = base_url or _ollama_base_url()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    img_data = f"data:image/jpeg;base64,{b64}"
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": PROMPT,
                        "images": [img_data],
                    }
                ],
            },
        )
        r.raise_for_status()
        data = r.json()
        content = data.get("message", {}).get("content", "{}")
        return _parse_ai_response(content)


def analyze_receipt(image_bytes: bytes) -> dict[str, Any]:
    """
    Analyze receipt image. Tries Ollama (llava/llama3.2-vision), then Gemini if configured.
    Returns: {"amount": float, "description": str, "date": str}
    """
    # Try Ollama first
    if HAS_OLLAMA:
        try:
            return analyze_receipt_ollama(image_bytes)
        except Exception:
            pass

    try:
        return analyze_receipt_via_api(image_bytes, base_url=_ollama_base_url())
    except httpx.TimeoutException as e:
        raise ValueError(f"Ollama timeout (vision model may be slow): {e}") from e
    except httpx.ConnectError as e:
        raise ValueError(f"Ollama unreachable at {_ollama_base_url()}: {e}") from e
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Vision analysis failed: {e}") from e
