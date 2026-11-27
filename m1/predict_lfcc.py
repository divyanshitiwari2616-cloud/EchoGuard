import numpy as np
import joblib
import sys

from extract_lfcc import extract_features

model = joblib.load("best_lfcc_model.pkl")


def predict_audio(audio_path):

    features = extract_features(audio_path)
    features = features.reshape(1, -1)

    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]

    real_prob = probabilities[
        list(model.classes_).index(0)
    ]

    fake_prob = probabilities[
        list(model.classes_).index(1)
    ]

    print("\n===== VOICE DETECTION RESULT =====")

    print("Prediction:", "FAKE" if prediction == 1 else "REAL")

    print(f"Real score: {real_prob:.2%}")
    print(f"Fake score: {fake_prob:.2%}")

    return prediction, fake_prob


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Please provide an audio file path.")

    else:
        predict_audio(sys.argv[1])