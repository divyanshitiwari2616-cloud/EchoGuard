import os
import numpy as np
import tensorflow as tf
import requests

from features_v3 import load_audio, extract_logmel, chunk_audio, fix_length


# --------------------------------------------------
# Model path
# --------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "model_v4_3ch.h5")

print("Loading voice authenticity model...")

_model = tf.keras.models.load_model(
    MODEL_PATH,
    compile=False
)

print("Model loaded successfully.")


# --------------------------------------------------
# M3-compatible prediction function
# --------------------------------------------------

def predict_voice(audio_path):

    try:
        # Load audio using the SAME preprocessing used during training
        audio = load_audio(audio_path)

        if audio is None or len(audio) == 0:
            return {
                "score": None,
                "label": "error_no_audio"
            }

        # Split longer audio into 2-second chunks
        chunks = chunk_audio(audio)

        # If audio is shorter than one accepted chunk,
        # process it as one padded 2-second clip
        if not chunks:
            chunks = [fix_length(audio)]

        # Extract EXACT training features
        batch = np.stack(
            [extract_logmel(chunk) for chunk in chunks],
            axis=0
        ).astype(np.float32)

        print(f"Feature batch shape: {batch.shape}")

        # Predict
        probabilities = _model.predict(
            batch,
            verbose=0
        ).reshape(-1)

        # Average predictions if there are multiple chunks
        score = float(np.mean(probabilities))

        # Same threshold used for the final evaluation
        label = (
            "likely_cloned"
            if score >= 0.50
            else "likely_real"
        )

        return {
            "score": round(score, 4),
            "label": label
        }

    except FileNotFoundError:
        return {
            "score": None,
            "label": "error_file_not_found"
        }

    except Exception as e:
        print("PREDICTION ERROR:", e)

        return {
            "score": None,
            "label": "error"
        }


# --------------------------------------------------
# Direct testing
# --------------------------------------------------

def send_to_m3(voice_score, m2_result):
    url = "http://127.0.0.1:8000/analyze-combined"

    payload = {
        "m1_voice_score": voice_score,
        "m2_result": m2_result
    }

    response = requests.post(
        url,
        json=payload
    )

    print("\nM3 Response:")
    print(response.status_code)
    print(response.json())


if __name__ == "__main__":

    print("\nM1 Voice Authenticity Predictor")
    print("--------------------------------")

    audio_path = input(
        "Enter audio file path: "
    ).strip().strip('"')

    result = predict_voice(audio_path)

    print("\nM1 Prediction:")
    print(result)