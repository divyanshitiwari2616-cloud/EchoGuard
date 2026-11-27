import numpy as np
import librosa
import joblib
import soundfile as sf
import tempfile
import os
import sys
import json
from pathlib import Path

from extract_lfcc import extract_features


# ==============================
# MODEL LOADING
# ==============================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "best_lfcc_model.pkl"

model = joblib.load(MODEL_PATH)


# ==============================
# SETTINGS
# ==============================

SR = 16000
SEGMENT_LENGTH = 32000
THRESHOLD = 0.50


# ==============================
# AUDIO PREDICTION
# ==============================

def predict_audio(audio_path):

    audio, sr = librosa.load(
        audio_path,
        sr=SR,
        mono=True
    )

    fake_scores = []

    print("\n===== SEGMENT-WISE DETECTION =====")

    for start in range(0, len(audio), SEGMENT_LENGTH):

        segment = audio[start:start + SEGMENT_LENGTH]

        # Skip very short segments
        if len(segment) < SR:
            continue

        # Skip silent segments
        if np.sqrt(np.mean(segment ** 2)) < 0.001:
            continue

        # Fix segment length to 2 seconds
        segment = librosa.util.fix_length(
            segment,
            size=SEGMENT_LENGTH
        )

        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp:

            temp_path = temp.name

        try:

            sf.write(
                temp_path,
                segment,
                SR,
                subtype="FLOAT"
            )

            # Extract LFCC features
            features = extract_features(temp_path)

            features = features.reshape(1, -1)

            # Predict probabilities
            probabilities = model.predict_proba(
                features
            )[0]

            fake_prob = float(
                probabilities[
                    list(model.classes_).index(1)
                ]
            )

            fake_scores.append(fake_prob)

            prediction = (
                "FAKE"
                if fake_prob >= THRESHOLD
                else "REAL"
            )

            print(
                f"Segment {start // SEGMENT_LENGTH + 1}: "
                f"{prediction} | "
                f"Fake score: {fake_prob:.2%}"
            )

        finally:

            if os.path.exists(temp_path):
                os.remove(temp_path)


    # ==============================
    # HANDLE EMPTY OR SILENT AUDIO
    # ==============================

    if not fake_scores:

        return {
            "prediction": "UNKNOWN",
            "fake_score": None,
            "real_score": None,
            "segments_analyzed": 0,
            "error": "No usable audio segments found."
        }


    # ==============================
    # FINAL PREDICTION
    # ==============================

    final_fake = float(np.mean(fake_scores))

    final_real = 1.0 - final_fake

    prediction = (
        "FAKE"
        if final_fake >= THRESHOLD
        else "REAL"
    )

    print("\n===== FINAL PREDICTION =====")

    print("Segments analyzed:", len(fake_scores))

    print("Prediction:", prediction)

    print(f"Real score: {final_real:.2%}")

    print(f"Fake score: {final_fake:.2%}")


    # ==============================
    # BACKEND RESPONSE
    # ==============================

    return {
        "prediction": prediction,
        "fake_score": final_fake,
        "real_score": final_real,
        "segments_analyzed": len(fake_scores)
    }


# ==============================
# TERMINAL EXECUTION
# ==============================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print("Please provide an audio file path.")

    else:

        result = predict_audio(sys.argv[1])

        print("\n===== BACKEND RESPONSE =====")

        print(json.dumps(result, indent=4))