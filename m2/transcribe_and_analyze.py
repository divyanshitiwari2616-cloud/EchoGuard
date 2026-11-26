
"""
EchoGuard - M2
Persistent Whisper worker + scam analysis.

stdout contains ONLY JSON results.
Diagnostic messages go to stderr.
"""

import sys
import json

from scam_classifier import analyze_text

_model = None


def _get_model():
    global _model

    if _model is None:
        from faster_whisper import WhisperModel

        print(
            "Loading Whisper model...",
            file=sys.stderr,
            flush=True
        )

        _model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=1
        )

        print(
            "Whisper model loaded.",
            file=sys.stderr,
            flush=True
        )

    return _model


def transcribe(audio_path: str) -> tuple:
    model = _get_model()

    segments, info = model.transcribe(
        audio_path,
        beam_size=1,
        vad_filter=True
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
    )

    return text, info.language


def analyze_audio(audio_path: str) -> dict:
    text, language = transcribe(audio_path)

    result = analyze_text(text)

    return {
        "transcript": text,
        "language": language,
        "risk": result.get("risk", "Low"),
        "score": result.get("score", 0),
        "reasons": result.get("reasons", [])
    }


def worker_mode():
    """Keep one process alive and reuse the loaded model."""

    print(
        "M2 worker starting...",
        file=sys.stderr,
        flush=True
    )

    _get_model()

    print(
        "M2 worker ready.",
        file=sys.stderr,
        flush=True
    )

    for line in sys.stdin:
        audio_path = line.strip()

        if not audio_path:
            continue

        try:
            result = analyze_audio(audio_path)

        except Exception as e:
            result = {"error": str(e)}

        print(json.dumps(result), flush=True)


if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker_mode()

    elif len(sys.argv) < 2:
        print(json.dumps({"error": "No audio file provided"}))
        sys.exit(1)

    else:
        try:
            result = analyze_audio(sys.argv[1])
            print(json.dumps(result), flush=True)

        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)
            sys.exit(1)
