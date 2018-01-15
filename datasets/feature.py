# -*- coding: utf-8 -*-

import pysptk
import pyworld
import numpy as np
from nnmnkwii.preprocessing.f0 import interp1d
from nnmnkwii.util import apply_delta_windows
from nnmnkwii.io import hts
import librosa
from hparams import hparams


def get_mgc_lf0_uv_bap(wav_path, label_path=None):
    x, fs = librosa.load(wav_path, sr=hparams.sample_rate)
    x = x.astype(np.float64)
    _f0, time_axis = pyworld.dio(x, fs, frame_period=hparams.frame_period)
    f0 = pyworld.stonemask(x, _f0, time_axis, fs)
    spectrogram = pyworld.cheaptrick(x, f0, time_axis, fs)

    mgc = pysptk.sp2mc(spectrogram, order=hparams.mgc_order, alpha=pysptk.util.mcepalpha(fs))

    f0 = f0[:, None]
    lf0 = f0.copy()
    nonzero_indices = np.nonzero(f0)
    lf0[nonzero_indices] = np.log(f0[nonzero_indices])
    # uv = (lf0 != 0).astype(np.float32)

    # continuous lf0 or not
    lf0 = interp1d(lf0, kind='slinear')

    # order 59
    # mgc dim 60*3
    # mgc = apply_delta_windows(mgc, hparams.windows)
    # # lf0 dim 1*3
    # lf0 = apply_delta_windows(lf0, hparams.windows)

    features = np.hstack((mgc, lf0))

    # cut silence frames by hts alignment
    if label_path is not None:
        labels = hts.load(label_path)
        features = features[:labels.num_frames()]
        indices = labels.silence_frame_indices()
        features = np.delete(features, indices, axis=0)

    return features.astype(np.float32)
