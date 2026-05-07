#!/usr/bin/env python3

import sys

from core.llm import stream_response, MODELS, ensure_ollama_running, load_model
from core.tts import speak, warmup
from skills import route


WAKE_WORD          = "alice"
WAKE_MODEL_SIZE    = "base"
COMMAND_MODEL_SIZE = "small"


def choose_model() -> str:
    print("\nChoose a model:")
    keys = list(MODELS.keys())
    for i, key in enumerate(keys, 1):
        print(f"  {i}) {MODELS[key]}")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return keys[0]
        if choice == "2":
            return keys[1]
        print("Please enter 1 or 2.")


def choose_input_mode() -> str:
    print("\nChoose input mode:")
    print("  v) Voice  — speak to Alice using the wake word")
    print("  t) Text   — type commands in the console")
    while True:
        choice = input("Enter v or t: ").strip().lower()
        if choice in ("v", "t"):
            return choice
        print("Please enter v or t.")


def _handle_command(command: str, history: list[dict], model: str) -> str:
    """Route to a skill or fall back to the LLM. Returns the full response text."""
    result = route(command)
    if result is not None:
        print(f"Alice: {result.response}\n")
        speak(result.response)
        return result.response

    print("Alice:", end=" ", flush=True)
    full = ""
    for sentence in stream_response(command, history, model):
        print(sentence, end=" ", flush=True)
        speak(sentence)
        full += sentence + " "
    print("\n")
    return full.strip()


def run_text_loop(model: str) -> None:
    history: list[dict] = []
    print('\nType your message and press Enter. Type "exit" or press Ctrl+C to quit.\n')
    try:
        while True:
            command = input("You: ").strip()
            if not command:
                continue
            if command.lower() in ("exit", "quit"):
                print("Goodbye.")
                break

            full = _handle_command(command, history, model)
            history.append({"role": "user",      "content": command})
            history.append({"role": "assistant",  "content": full})
    except KeyboardInterrupt:
        print("\nGoodbye.")


def run_voice_loop(model: str) -> None:
    import queue
    import whisper
    import sounddevice as sd
    from core.audio import collect_utterance, transcribe, SAMPLE_RATE, CHUNK_SIZE

    print(f"\nLoading Whisper '{WAKE_MODEL_SIZE}' (wake word)…")
    wake_model = whisper.load_model(WAKE_MODEL_SIZE)
    print(f"Loading Whisper '{COMMAND_MODEL_SIZE}' (commands)…")
    command_model = whisper.load_model(COMMAND_MODEL_SIZE)
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
            audio = collect_utterance(audio_q)
            if audio is None:
                continue

            wake_text = transcribe(audio, wake_model)
            wake_idx = wake_text.lower().find(WAKE_WORD)
            if wake_idx == -1:
                continue

            print("[Wake word detected]")
            speak("Yes?")

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
            full = _handle_command(command, history, model)
            history.append({"role": "user",      "content": command})
            history.append({"role": "assistant",  "content": full})

    except KeyboardInterrupt:
        print("\nGoodbye.")
    finally:
        stream.stop()
        stream.close()


def main():
    ensure_ollama_running()

    model = choose_model()
    mode  = choose_input_mode()

    print(f"\nStarting Alice with model '{model}' in {'voice' if mode == 'v' else 'text'} mode.")
    load_model(model)
    print("Warming up voice…")
    warmup()

    if mode == "t":
        run_text_loop(model)
    else:
        run_voice_loop(model)


if __name__ == "__main__":
    main()
