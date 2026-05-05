#!/usr/bin/env python3

import sys
import queue
import whisper
import sounddevice as sd

from core.audio import collect_utterance, transcribe, SAMPLE_RATE, CHUNK_SIZE
from core.llm import stream_response
from core.tts import speak, warmup

WAKE_WORD          = "alice"
WAKE_MODEL_SIZE    = "base"
COMMAND_MODEL_SIZE = "small"


def main():
    print(f"Loading Whisper '{WAKE_MODEL_SIZE}' (wake word)…")
    wake_model = whisper.load_model(WAKE_MODEL_SIZE)
    print(f"Loading Whisper '{COMMAND_MODEL_SIZE}' (commands)…")
    command_model = whisper.load_model(COMMAND_MODEL_SIZE)
    print("Warming up voice…")
    warmup()
    print("Ready.\n")

    audio_q: queue.Queue = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(f"Audio warning: {status}", file=sys.stderr)
        audio_q.put(indata.copy().flatten())

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK_SIZE,
        callback=callback,
    )
    stream.start()

    history: list[dict] = []
    print(f'Listening for wake word "Alice"… (Ctrl+C to quit)\n')

    try:
        while True:
            # Wait for an utterance containing the wake word
            audio = collect_utterance(audio_q)
            if audio is None:
                continue

            wake_text = transcribe(audio, wake_model)
            wake_idx = wake_text.lower().find(WAKE_WORD)
            if wake_idx == -1:
                continue

            print("[Wake word detected]")
            speak("Yes?")

            # Get the command: re-transcribe with the more accurate model if
            # the command was in the same utterance, or collect a new utterance
            suffix = wake_text[wake_idx + len(WAKE_WORD):].strip(" ,.-")

            if suffix:
                command_text = transcribe(audio, command_model)
                cmd_idx = command_text.lower().find(WAKE_WORD)
                command = (
                    command_text[cmd_idx + len(WAKE_WORD):].strip(" ,.-")
                    if cmd_idx != -1 else suffix
                )
            else:
                print("Listening for your instruction…")
                audio = collect_utterance(audio_q)
                if audio is None:
                    print("No instruction heard.\n")
                    continue
                command = transcribe(audio, command_model)

            if not command:
                print("(nothing transcribed)\n")
                continue

            print(f"You:   {command}")
            print("Alice:", end=" ", flush=True)

            full = ""
            for sentence in stream_response(command, history):
                print(sentence, end=" ", flush=True)
                speak(sentence)
                full += sentence + " "
            print("\n")

            history.append({"role": "user",      "content": command})
            history.append({"role": "assistant",  "content": full.strip()})

    except KeyboardInterrupt:
        print("\nGoodbye.")
    finally:
        stream.stop()
        stream.close()


if __name__ == "__main__":
    main()
