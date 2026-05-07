import re
import sys
import json
import time
import subprocess
import requests

OLLAMA_BASE = "http://localhost:11434"
OLLAMA_URL  = f"{OLLAMA_BASE}/api/chat"

MODELS = {
    "qwen3:14b": "qwen3:14b (recommended for 32 GB RAM / 8 GB VRAM)",
    "llama3.2":  "llama3.2  (recommended for 16 GB RAM / 4 GB VRAM)",
}

SYSTEM_PROMPT = """\
You are Alice, a sharp and friendly voice assistant.
Follow these rules strictly:
- Reply in 1 to 3 complete sentences of plain spoken English — no more.
- Never use markdown: no asterisks, no hashes, no bullet points, no headers.
- No filler openers like "Sure!", "Certainly!", or "Great question!".
- Never defer: do not say "let me check", "let me look that up", or anything implying you need to retrieve information. Answer immediately from what you already know.
- When asked about past conversations, answer directly from the message history you have been given — never imply you need to search for it.
- If you are unsure, say so in one sentence.
- Remember the conversation — refer back to earlier messages when relevant.
- This output is read aloud, so write naturally spoken words only.\
"""

_SENT_END   = re.compile(r'(?<=[.!?])\s+')
_THINK_DONE = re.compile(r'<think>.*?</think>', re.DOTALL)
_THINK_OPEN = re.compile(r'<think>.*$',         re.DOTALL)


def _ollama_ready() -> bool:
    try:
        requests.get(OLLAMA_BASE, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False


def ensure_ollama_running() -> None:
    if _ollama_ready():
        return
    print("Ollama is not running — starting it…")
    kwargs: dict = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        subprocess.Popen(["ollama", "serve"], **kwargs)
    except FileNotFoundError:
        print("Error: 'ollama' not found in PATH. Please start Ollama manually.")
        return
    for _ in range(30):
        time.sleep(0.5)
        if _ollama_ready():
            print("Ollama is ready.")
            return
    print("Warning: Ollama may not have started in time.")


def load_model(model: str) -> None:
    print(f"Loading model '{model}'…")
    try:
        requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": model, "prompt": "", "keep_alive": "10m"},
            timeout=180,
        )
        print(f"Model '{model}' is ready.")
    except requests.exceptions.RequestException as exc:
        print(f"Warning: could not pre-load model: {exc}")


def flush_sentences(buf: str) -> tuple[list[str], str]:
    """Split buf into (finished_sentences, leftover)."""
    parts = _SENT_END.split(buf)
    return (parts[:-1], parts[-1]) if len(parts) > 1 else ([], buf)


def strip_thinking(text: str) -> str:
    # """Remove qwen3 <think>…</think> reasoning traces (complete or partial)."""
    text = _THINK_DONE.sub('', text)
    text = _THINK_OPEN.sub('', text)
    return text


def stream_response(user_text: str, history: list[dict], model: str = "llama3.2"):
    """Yield one complete sentence at a time as the LLM generates output."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_text},
    ]
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model":    model,
                "messages": messages,
                "stream":   True,
                "think":    False,
            },
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        yield "Sorry, Ollama doesn't seem to be running."
        return

    buf = ""
    for line in resp.iter_lines():
        if not line:
            continue
        data = json.loads(line)
        buf += data.get("message", {}).get("content", "")
        buf = strip_thinking(buf)
        sentences, buf = flush_sentences(buf)
        for s in sentences:
            if s.strip():
                yield s.strip()
        if data.get("done"):
            break

    tail = strip_thinking(buf).strip()
    if tail:
        yield tail
