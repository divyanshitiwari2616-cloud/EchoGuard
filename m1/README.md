# EchoGuard – AI Voice Detection Module

## Overview

This module detects real and AI-generated voices using Linear Frequency Cepstral Coefficients (LFCC) and a Support Vector Machine (SVM) classifier.

## Model Architecture

- Audio sampling rate: 16,000 Hz
- Segment duration: 2 seconds
- LFCC coefficients: 20
- Additional features: Delta and Delta-Delta
- Total input features: 120
- Feature scaling: StandardScaler
- Classifier: SVM with RBF kernel
- Decision threshold: 0.50
- Multi-segment prediction: Average fake score

## Model Performance

| Metric | Result |
|---|---:|
| Training samples | 2,100 |
| Validation samples | 450 |
| Testing samples | 450 |
| Internal testing accuracy | 100% |
| Precision | 100% |
| Recall | 100% |
| F1 score | 100% |

## Independent Audio Testing

| Audio | Prediction | Score |
|---|---|---:|
| Human voice | REAL | 83.70% |
| ElevenLabs AI voice | FAKE | 70.15% |

## Installation

Install the dependencies using:

`pip install -r requirements.txt`

Use the same Python environment version as the training environment where possible.

## Required Files

- best_lfcc_model.pkl
- extract_lfcc.py
- predict_lfcc_segments.py
- requirements.txt

## Backend Integration

Import the prediction function:

`from predict_lfcc_segments import predict_audio`

Pass the uploaded audio file path:

`result = predict_audio("uploaded_audio.wav")`

The returned dictionary contains:

- prediction: REAL, FAKE or UNKNOWN
- fake_score: Aggregated fake score
- real_score: Aggregated real score
- segments_analyzed: Number of usable segments

The backend should handle UNKNOWN predictions and exceptions caused by invalid audio files.

## Supported Audio Formats

- WAV
- MP3

## Hardware Requirements

- CPU-based inference
- No GPU required
- No TensorFlow required for LFCC inference
- No external API required

## Limitations

- The 100% accuracy was obtained on an internal randomly split dataset.
- The previous CNN achieved 82.63% on a different test dataset; direct improvement has not yet been independently established.
- Larger independent dataset evaluation is pending.
- Prediction scores are not guaranteed probabilities of voice authenticity.
- Averaging segment scores may overlook short synthetic portions in longer recordings.

## Current Status

Model training, feature extraction, preliminary evaluation, multi-segment detection and backend-compatible prediction have been completed. The module is ready for integration, with further validation pending.