"""
EchoGuard - M2
Audio -> Whisper Transcript -> Scam Analysis

stdout contains ONLY the final JSON result.
Diagnostic messages are sent to stderr.
"""

import sys
import json

from scam_classifier import analyze_text

_model = None


def _get_model(model_size: str = "small"):
    global _model

    if _model is None:
        from faster_whisper import WhisperModel

        print(
            "Loading Whisper model...",
            file=sys.stderr,
            flush=True
        )

        _model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"
        )

        print(
            "Whisper model loaded.",
            file=sys.stderr,
            flush=True
        )

    return _model


def transcribe(audio_path: str) -> tuple:
    model = _get_model()

    hint = (
        "OTP, PIN, CVV, KYC, RBI, bank account, "
        "verification code, UPI"
    )

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        initial_prompt=hint
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


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            json.dumps({
                "error": "No audio file provided"
            }),
            flush=True
        )
        sys.exit(1)

    audio_path = sys.argv[1]

    try:
        result = analyze_audio(audio_path)

        print(
            json.dumps(result),
            flush=True
        )

    except Exception as e:

        print(
            json.dumps({
                "error": str(e)
            }),
            flush=True
        )

        sys.exit(1)