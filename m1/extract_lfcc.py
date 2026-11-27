import numpy as np
import librosa
from scipy.fft import dct

SR = 16000
N_FFT = 512
N_FILTERS = 40
N_LFCC = 20

# Create linear-frequency filter bank
frequencies = np.linspace(
    0, SR / 2, N_FFT // 2 + 1
)

edges = np.linspace(
    0, SR / 2, N_FILTERS + 2
)

filters = np.zeros(
    (N_FILTERS, len(frequencies))
)

for i in range(N_FILTERS):

    left, center, right = edges[i:i+3]

    filters[i] = np.maximum(
        0,
        np.minimum(
            (frequencies - left) / (center - left),
            (right - frequencies) / (right - center)
        )
    )


def extract_features(path):

    audio, sr = librosa.load(
        path, sr=SR, mono=True
    )

    audio = librosa.util.fix_length(
        audio, size=32000
    )

    spectrum = np.abs(
        librosa.stft(
            audio,
            n_fft=N_FFT,
            hop_length=160,
            win_length=400
        )
    ) ** 2

    energies = filters @ spectrum

    lfcc = dct(
        np.log(energies + 1e-10),
        type=2,
        axis=0,
        norm="ortho"
    )[:N_LFCC]

    delta = librosa.feature.delta(lfcc)

    delta2 = librosa.feature.delta(
        lfcc, order=2
    )

    features = np.vstack([
        lfcc, delta, delta2
    ])

    return np.concatenate([
        features.mean(axis=1),
        features.std(axis=1)
    ])