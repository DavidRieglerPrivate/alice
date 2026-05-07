# Alice

A fully local voice assistant. Say "Alice" to wake it, speak your command, and hear the response — all running on your machine with no cloud calls.

**Pipeline:** Microphone → Whisper STT → Ollama LLM → Piper TTS

---

## Requirements

**Hardware**
- Microphone (voice mode only)
- Nvidia GPU recommended (speeds up Whisper and Ollama inference)

**Software**
- Python 3.10+
- [Ollama](https://ollama.com) installed (Alice will start it automatically if it isn't running)
- [Piper](https://github.com/rhasspy/piper) executable placed at `piper/piper.exe`
- A Piper voice model placed at `voices/en_US-hfc_female-medium.onnx`

---

## Setup

```bash
# Install Python dependencies
pip install -r requirements.txt
```

The LLM model will be pulled automatically on first run once you select it at startup.

---

## Usage

```bash
python alice.py
```

On startup, Alice will ask two questions:

1. **Which model to use:**
   - `qwen3:14b` — better quality, requires ~16 GB RAM / 10 GB VRAM
   - `llama3.2` — lighter, requires ~8 GB RAM / 4 GB VRAM

2. **Which input mode:**
   - **Voice** — wake word detection + spoken interaction
   - **Text** — type commands in the console (no microphone needed)

In voice mode, Alice loads two Whisper models and warms up the TTS engine, then listens for the wake word.

- **Wake + command in one utterance:** "Alice, what's the capital of France?"
- **Wake then speak:** Say "Alice", wait for the "Yes?" prompt, then give your command.

Press `Ctrl+C` to exit.

---

## Skills

Alice routes commands to built-in skills before falling back to the LLM.

| Skill | Example phrases |
|---|---|
| **Calculator** | "what's 15% of 80", "square root of 144", "2 to the power of 10" |
| **Open file** | "open my resume", "find budget.xlsx", "open the project proposal" |
| **Launch app** | "open Chrome", "launch VS Code", "open Spotify" |
| **Close app** | "close Notepad", "kill Chrome" |
| **Memory** | "wipe memory", "clear history", "forget everything" |
| **General Q&A** | anything else - Ollama LLM with conversation context |

---

## Memory

Alice remembers your conversations across sessions. The last 10 exchanges are loaded as context at startup so Alice can refer back to earlier parts of your conversation.

Memory is stored locally at `memory/memory.json`.

---

## Configuration

Edit constants at the top of each module to customize behavior:

| File | Constant | Default | Description |
|---|---|---|---|
| `alice.py` | `WAKE_MODEL_SIZE` | `"base"` | Whisper model for wake detection (faster) |
| `alice.py` | `COMMAND_MODEL_SIZE` | `"small"` | Whisper model for commands (more accurate) |
| `core/audio.py` | `SILENCE_RMS` | `0.01` | RMS threshold below which audio is treated as silence |
| `core/audio.py` | `SILENCE_DURATION` | `1.5` | Seconds of silence that end an utterance |
| `core/tts.py` | `VOLUME` | `0.35` | Playback volume (0.0–1.0) |

---

## Architecture

```
alice.py              — startup, model/mode selection, main loop
core/
  audio.py            — microphone capture, silence detection, Whisper transcription
  llm.py              — Ollama streaming, sentence splitting, think-tag stripping
  tts.py              — Piper TTS subprocess, audio playback
  memory.py           — persistent conversation history (JSON)
skills/
  router.py           — regex-based command routing
  calculator.py       — safe AST math evaluation with natural language parsing
  file_ops.py         — file search and open across user directories
  launch_app.py       — Windows app launching and closing
  memory_ops.py       — memory wipe handler
```

Responses stream sentence-by-sentence so Piper starts speaking before the LLM finishes generating.
