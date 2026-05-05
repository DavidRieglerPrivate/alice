import queue
import numpy as np

SAMPLE_RATE         = 16000
CHUNK_DURATION      = 0.1
CHUNK_SIZE          = int(SAMPLE_RATE * CHUNK_DURATION)
SILENCE_RMS         = 0.01
SILENCE_DURATION    = 1.5
MIN_SPEECH_DURATION = 0.3


def rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk ** 2)))


def collect_utterance(audio_q: queue.Queue) -> np.ndarray | None:
    """Block until a speech utterance ends (silence after speech). Returns PCM or None."""
    chunks: list[np.ndarray] = []
    silent_chunks = 0
    speaking = False
    silence_limit = int(SILENCE_DURATION / CHUNK_DURATION)
    min_chunks    = int(MIN_SPEECH_DURATION / CHUNK_DURATION)

    while True:
        chunk = audio_q.get()
        level = rms(chunk)
        if level > SILENCE_RMS:
            speaking = True
            silent_chunks = 0
            chunks.append(chunk)
        elif speaking:
            chunks.append(chunk)
            silent_chunks += 1
            if silent_chunks >= silence_limit:
                break

    speech_chunks = len(chunks) - silent_chunks
    if speech_chunks < min_chunks:
        return None
    return np.concatenate(chunks)


def transcribe(audio: np.ndarray, model) -> str:
    result = model.transcribe(audio, language="en", fp16=False)
    return result["text"].strip()
