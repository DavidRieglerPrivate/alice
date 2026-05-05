import subprocess
import numpy as np
import sounddevice as sd
from pathlib import Path

_ROOT       = Path(__file__).parent.parent
PIPER_EXE   = _ROOT / "piper" / "piper.exe"
VOICE_MODEL = _ROOT / "voices" / "en_US-hfc_female-medium.onnx"
SAMPLE_RATE = 22050
VOLUME      = 0.35   # 1.0 = full device volume; lower = quieter

_PIPER_CMD  = [str(PIPER_EXE), "--model", str(VOICE_MODEL), "--output_raw"]


def warmup() -> None:
    """Run a silent synthesis at startup so the ONNX model is hot for the first real call."""
    proc = subprocess.Popen(_PIPER_CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc.communicate(b".")   # minimal text; output is discarded, not played


def speak(text: str) -> None:
    """Synthesise text with Piper and block until playback finishes."""
    proc = subprocess.Popen(_PIPER_CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw, _ = proc.communicate(text.encode())
    if raw:
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0 * VOLUME
        sd.play(audio, samplerate=SAMPLE_RATE)
        sd.wait()
