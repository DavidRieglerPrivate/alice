# Alice

A fully local voice assistant. Say "Alice" to wake it, speak your command, and hear the response — all running on your machine with no cloud calls.

**Pipeline:** Microphone → Whisper STT → Ollama LLM → Piper TTS

---

## Requirements

**Hardware**
- Microphone
- GPU recommended (speeds up Whisper and Ollama inference)

**Software**
- Python 3.10+
- [Ollama](https://ollama.com) running locally with the `qwen3:14b` model pulled
- [Piper](https://github.com/rhasspy/piper) executable placed at `piper/piper.exe`
- A Piper voice model placed at `voices/en_US-hfc_female-medium.onnx`

---

## Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Pull the LLM (requires Ollama to be installed and running)
ollama pull qwen3:14b
```

Download Piper from the [releases page](https://github.com/rhasspy/piper/releases) and a voice model from the [Hugging Face collection](https://huggingface.co/rhasspy/piper-voices). Place them at:

```
alice/
├── piper/
│   └── piper.exe
└── voices/
    └── en_US-hfc_female-medium.onnx
```

---

## Usage

```bash
python alice.py
```

On startup, Alice loads two Whisper models and warms up the TTS engine, then listens for the wake word.

- **Wake + command in one utterance:** "Alice, what's the capital of France?"
- **Wake then speak:** Say "Alice", wait for the "Yes?" prompt, then give your command.

Press `Ctrl+C` to exit.

---

## Configuration

Edit constants at the top of each module to customize behavior:

| File | Constant | Default | Description |
|---|---|---|---|
| `alice.py` | `WAKE_MODEL_SIZE` | `"base"` | Whisper model for wake detection (faster) |
| `alice.py` | `COMMAND_MODEL_SIZE` | `"small"` | Whisper model for commands (more accurate) |
| `core/audio.py` | `SILENCE_RMS` | `0.01` | RMS threshold below which audio is treated as silence |
| `core/audio.py` | `SILENCE_DURATION` | `1.5` | Seconds of silence that end an utterance |
| `core/llm.py` | `LLM_MODEL` | `"qwen3:14b"` | Ollama model name |
| `core/tts.py` | `VOLUME` | `0.35` | Playback volume (0.0–1.0) |

---

## Architecture

```
core/audio.py   — microphone capture, silence detection, Whisper transcription
core/llm.py     — Ollama streaming, sentence splitting, Qwen3 think-tag stripping
core/tts.py     — Piper TTS subprocess, audio playback
alice.py        — main loop: wake detection → command → LLM → speech
```

Responses stream sentence-by-sentence so Piper starts speaking before the LLM finishes generating.
