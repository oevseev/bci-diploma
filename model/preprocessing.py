from abc import ABC

import numpy as np
import scipy.signal
from sklearn.decomposition import FastICA


class PreprocessingStrategy(ABC):
    def __init__(self, batch_size=16, sample_rate=128):
        self.batch_size = batch_size
        self.sample_rate = sample_rate

    def preprocess_batch(self, batch):
        return batch


class ConcretePreprocessingStrategy(PreprocessingStrategy):
    def __init__(self, bandpass_lcf=0.4, bandpass_hcf=30.0, subsample_rate=2, num_removed_comps=4):
        super().__init__(batch_size=512)

        self.bandpass_lcf = bandpass_lcf
        self.bandpass_hcf = bandpass_hcf
        self.subsample_rate = subsample_rate
        self.num_removed_comps = num_removed_comps

    def preprocess_batch(self, batch):
        batch = np.array(batch)

        res = self._bandpass(batch, self.bandpass_lcf, self.bandpass_hcf)
        res = self._subsample(res, self.subsample_rate)
        res = self._ica(res, self.num_removed_comps)

        return res.tolist()

    def _bandpass(self, batch, lcf, hcf):
        nyquist_freq = self.sample_rate / 2
        b, a = scipy.signal.butter(5, [lcf / nyquist_freq, hcf / nyquist_freq], btype='band')
        res = scipy.signal.lfilter(b, a, batch)
        return res

    def _subsample(self, batch, k=2):
        return batch[::k].repeat(k, axis=0)

    def _ica(self, batch, num_comps=4):
        ica = FastICA(n_components=batch.shape[1], max_iter=300)
        comps = ica.fit_transform(batch)
        m = (-np.abs(comps)).min(axis=0)
        selected = np.argsort(m)[:num_comps]
        comps[:, selected] = 0
        return ica.inverse_transform(comps)
