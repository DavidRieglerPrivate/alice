import json
import os
from datetime import datetime

_MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "memory", "memory.json")
_MEMORY_PATH = os.path.normpath(_MEMORY_PATH)

_current_session_id: str = ""


def _load() -> dict:
    if not os.path.exists(_MEMORY_PATH):
        return {"conversations": []}
    try:
        with open(_MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"conversations": []}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(_MEMORY_PATH), exist_ok=True)
    with open(_MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_recent_exchanges(n: int = 10) -> list[dict]:
    """Return the last n exchanges as LLM-formatted messages (user + assistant pairs)."""
    data = _load()
    all_exchanges = []
    for session in data["conversations"]:
        all_exchanges.extend(session["exchanges"])
    messages = []
    for ex in all_exchanges[-n:]:
        messages.append({"role": "user",      "content": ex["user"]})
        messages.append({"role": "assistant",  "content": ex["assistant"]})
    return messages


def start_session() -> None:
    global _current_session_id
    _current_session_id = datetime.now().isoformat(timespec="seconds")
    data = _load()
    data["conversations"].append({"session_id": _current_session_id, "exchanges": []})
    _save(data)


def save_exchange(user: str, assistant: str) -> None:
    if not _current_session_id:
        return
    data = _load()
    for session in reversed(data["conversations"]):
        if session["session_id"] == _current_session_id:
            session["exchanges"].append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "user": user,
                "assistant": assistant,
            })
            break
    _save(data)


def wipe() -> None:
    _save({"conversations": []})
