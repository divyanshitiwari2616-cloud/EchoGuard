"""
features_v3.py

Audio feature extraction for the improved CNN model.

Features:
    Channel 1 -> Log-Mel spectrogram
    Channel 2 -> Delta (change over time)
    Channel 3 -> Delta-Delta (change of the change)

Output shape:
    (64, 101, 3)
"""

import numpy as np
import librosa
import soundfile as sf


# ============================================================
# AUDIO SETTINGS
# ============================================================

SAMPLE_RATE = 16000

# FoR-2seconds uses 2-second audio clips
CLIP_SAMPLES = SAMPLE_RATE * 2

# Mel-spectrogram settings
N_MELS = 64
N_FFT = 1024
HOP = 320

# Number of time frames
N_FRAMES = 1 + CLIP_SAMPLES // HOP


# ============================================================
# LOAD AUDIO
# ============================================================

def load_audio(path, sr=SAMPLE_RATE):
    """
    Load an audio file using librosa.

    Converts audio to:
        - mono
        - 16 kHz
    """
    audio, _ = librosa.load(
        path,
        sr=sr,
        mono=True
    )

    return audio


def load_audio_fast(path, sr=SAMPLE_RATE):
    """
    Faster audio loading using soundfile.

    If the file is not already at 16 kHz,
    it is resampled to 16 kHz.
    """

    audio, file_sr = sf.read(
        path,
        dtype="float32",
        always_2d=False
    )

    # Convert stereo/multi-channel audio to mono
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    # Resample if necessary
    if file_sr != sr:
        audio = librosa.resample(
            audio,
            orig_sr=file_sr,
            target_sr=sr
        )

    return audio


# ============================================================
# FIX AUDIO LENGTH
# ============================================================

def fix_length(audio, n=CLIP_SAMPLES):
    """
    Make every audio clip exactly 2 seconds.

    If longer:
        take the first 2 seconds.

    If shorter:
        zero-pad at the end.
    """

    if len(audio) >= n:
        return audio[:n]

    return np.pad(
        audio,
        (0, n - len(audio))
    )


# ============================================================
# EXTRACT 3-CHANNEL FEATURES
# ============================================================

def extract_logmel(audio):
    """
    Convert audio into a 3-channel feature representation.

    Channel 1:
        Log-Mel spectrogram

    Channel 2:
        Delta features

    Channel 3:
        Delta-delta features

    Final shape:
        (64, 101, 3)
    """

    # --------------------------------------------------------
    # Step 1: Make audio exactly 2 seconds
    # --------------------------------------------------------

    audio = fix_length(audio)

    # --------------------------------------------------------
    # Step 2: Calculate Mel spectrogram
    # --------------------------------------------------------

    mel = librosa.feature.melspectrogram(
        y=audio,
        sr=SAMPLE_RATE,
        n_fft=N_FFT,
        hop_length=HOP,
        n_mels=N_MELS,
        fmax=SAMPLE_RATE // 2
    )

    # --------------------------------------------------------
    # Step 3: Convert to log scale
    # --------------------------------------------------------

    mel = np.log(mel + 1e-6)

    # --------------------------------------------------------
    # Step 4: Force exactly N_FRAMES
    # --------------------------------------------------------

    if mel.shape[1] < N_FRAMES:

        mel = np.pad(
            mel,
            (
                (0, 0),
                (0, N_FRAMES - mel.shape[1])
            ),
            mode="edge"
        )

    else:

        mel = mel[:, :N_FRAMES]

    # --------------------------------------------------------
    # Step 5: Delta
    # --------------------------------------------------------
    # Shows how the spectral features change over time.

    delta = librosa.feature.delta(mel)

    # --------------------------------------------------------
    # Step 6: Delta-delta
    # --------------------------------------------------------
    # Shows how the changes themselves change over time.

    delta2 = librosa.feature.delta(
        mel,
        order=2
    )

    # --------------------------------------------------------
    # Step 7: Normalize each channel separately
    # --------------------------------------------------------

    mel = (
        mel - mel.mean()
    ) / (
        mel.std() + 1e-8
    )

    delta = (
        delta - delta.mean()
    ) / (
        delta.std() + 1e-8
    )

    delta2 = (
        delta2 - delta2.mean()
    ) / (
        delta2.std() + 1e-8
    )

    # --------------------------------------------------------
    # Step 8: Combine into 3 channels
    # --------------------------------------------------------

    features = np.stack(
        [
            mel,
            delta,
            delta2
        ],
        axis=-1
    )

    # Final shape:
    # 64 × 101 × 3

    return features.astype(np.float32)


# ============================================================
# SPLIT LONG AUDIO INTO 2-SECOND CHUNKS
# ============================================================

def chunk_audio(audio, chunk_len=CLIP_SAMPLES):
    """
    Split long audio into 2-second chunks.

    Very short final chunks are ignored.
    """

    chunks = []

    for start in range(
        0,
        len(audio),
        chunk_len
    ):

        piece = audio[
            start:start + chunk_len
        ]

        # Ignore chunks shorter than 1 second
        if len(piece) < chunk_len * 0.5:
            continue

        chunks.append(
            fix_length(piece)
        )

    return chunks