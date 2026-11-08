"""Core poetry analysis logic. Works with OpenAI and any OpenAI-compatible
open-weight endpoint (Groq, OpenRouter, Ollama, etc.).
Uses only the Python standard library (no openai package needed)."""
import json
import os
import re
import time
import urllib.error
import urllib.request

SYSTEM_PROMPT = """You are an expert literary critic and prosodist.
Analyze the poem the user gives you. Respond with ONLY a JSON object with exactly these keys:

{
  "form": "e.g. sonnet, free verse, ballad, haiku, villanelle",
  "meter": "e.g. iambic pentameter, trochaic tetrameter, none/irregular",
  "rhyme_scheme": "letters only, e.g. ABAB CDCD EFEF GG, or 'none'",
  "tone": ["1-3 adjectives"],
  "themes": ["2-4 short phrases"],
  "imagery": ["2-5 key images, quoted briefly from the poem"],
  "devices": ["literary devices used, each with a short example"],
  "summary": "2-3 sentences on what the poem is doing",
  "suggestions": ["2-4 concrete revision suggestions for the poet"]
}

Be accurate about meter and rhyme. If unsure, say so inside the value. No text outside the JSON."""

BACKENDS = {
    "openai": {
        "label": "OpenAI",
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    "open_weight": {
        "label": "Open-weight",
        "model": os.getenv("OPEN_MODEL", "llama3.1:8b"),
        "base_url": os.getenv("OPEN_BASE_URL", "http://localhost:11434/v1"),
        "api_key": os.getenv("OPEN_API_KEY", "ollama"),
    },
}

EXPECTED_KEYS = {
    "form", "meter", "rhyme_scheme", "tone", "themes",
    "imagery", "devices", "summary", "suggestions",
}


def _parse_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model output")
    return json.loads(text[start : end + 1])


def _post(cfg, payload, attempts=4):
    """POST with retries for dropped connections, rate limits and server errors."""
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    last = None
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg['api_key']}",
                "User-Agent": "poetry-analyzer/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            last = f"HTTP {e.code}: {body}"
            if e.code == 429 or e.code >= 500:
                wait = e.headers.get("Retry-After")
                time.sleep(min(float(wait), 30) if wait and wait.replace(".", "").isdigit() else 4 * attempt)
                continue
            raise RuntimeError(last) from None
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
            last = f"Network error: {e}"
            time.sleep(4 * attempt)
    raise RuntimeError(last)


def analyze_poem(poem: str, backend: str, temperature: float = 0.2) -> dict:
    """Returns {backend, model, ok, latency_s, result, raw, error}."""
    cfg = BACKENDS[backend]
    payload = {
        "model": cfg["model"],
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": poem.strip()},
        ],
    }
    out = {"backend": backend, "model": cfg["model"], "ok": False,
           "latency_s": None, "result": None, "raw": None, "error": None}
    time.sleep(1.5)  # small pause between requests to stay under free-tier limits
    start = time.time()
    try:
        if not cfg["api_key"]:
            raise RuntimeError("No API key set for this backend")
        try:
            data = _post(cfg, {**payload, "response_format": {"type": "json_object"}})
        except RuntimeError as first:
            if "HTTP 429" in str(first) or "HTTP 401" in str(first):
                raise
            data = _post(cfg, payload)  # some endpoints reject response_format
        out["latency_s"] = round(time.time() - start, 2)
        out["raw"] = data["choices"][0]["message"]["content"]
        parsed = _parse_json(out["raw"])
        out["result"] = parsed
        out["ok"] = EXPECTED_KEYS.issubset(parsed.keys())
        if not out["ok"]:
            out["error"] = f"Missing keys: {sorted(EXPECTED_KEYS - parsed.keys())}"
    except Exception as e:
        out["latency_s"] = out["latency_s"] or round(time.time() - start, 2)
        out["error"] = str(e)
    return out