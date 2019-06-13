import json
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime

import joblib
import numpy as np
from matplotlib.figure import Figure
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import model


def average_segments(stimuli, segments):
    d = defaultdict(list)
    for stimulus, segment in zip(stimuli, segments):
        d[stimulus].append(segment[1])
    return {k: np.mean(np.array(v), axis=0).flatten() for k, v in d.items()}


class Model(ABC):
    @abstractmethod
    def train_iteration(self, stimuli, segments, target):
        raise NotImplementedError

    @abstractmethod
    def get_probabilities(self, stimuli, segments):
        raise NotImplementedError


class RecordModel(Model):
    SCALE_FACTOR = 4.0

    def train_iteration(self, stimuli, segments, target):
        filename = "train_" + self._get_timestamp()
        self._plot(filename, stimuli, segments, target)
        self._dump(filename, {"stimuli": stimuli, "segments": segments, "target": target})

    def get_probabilities(self, stimuli, segments):
        filename = "work_" + self._get_timestamp()
        self._plot(filename, stimuli, segments, [])
        self._dump(filename, {"stimuli": stimuli, "segments": segments})
        return {x: 0.0 for x in stimuli}

    @staticmethod
    def _plot(filename, stimuli, segments, target):
        rows, cols = RecordModel._get_rows_cols(len(stimuli))
        fig = Figure(figsize=(RecordModel.SCALE_FACTOR * cols, RecordModel.SCALE_FACTOR * rows))
        axs = fig.subplots(rows, cols)

        for i, (stimulus, (start, data)) in enumerate(zip(stimuli, segments)):
            args = [str(stimulus), str(start)]
            if stimulus in target:
                args.append("relevant")
            caption = ', '.join(args)

            row, col = i // cols, i % cols
            axs[row, col].set_title(caption)
            axs[row, col].plot(data)

        directory = model.CONFIG_DIRECTORY / "images"
        directory.mkdir(parents=True, exist_ok=True)
        fig.savefig(directory / "{}.png".format(filename))

    @staticmethod
    def _dump(filename, data):
        directory = model.CONFIG_DIRECTORY / "data"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "{}.txt".format(filename)
        with open(path, 'w') as f:
            json.dump(data, f)

    @staticmethod
    def _get_timestamp():
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    @staticmethod
    def _get_rows_cols(n):
        rows, cur = 1, 2
        while cur * cur <= n:
            if n % cur == 0:
                rows = cur
            cur += 1
        return rows, n // rows


class LDAModel(RecordModel):
    def __init__(self):
        directory = model.CONFIG_DIRECTORY / "models"
        directory.mkdir(parents=True, exist_ok=True)
        self.filename = directory / "lda_model.joblib"

        if self.filename.exists():
            self._clf = joblib.load(self.filename)
        else:
            self._clf = make_pipeline(
                StandardScaler(),
                LinearDiscriminantAnalysis()
            )

        self._X, self._y = [], []

    def train_iteration(self, stimuli, segments, target):
        super().train_iteration(stimuli, segments, target)

        for stimulus, x in average_segments(stimuli, segments).items():
            self._X.append(x)
            self._y.append(int(stimulus in target))

    def get_probabilities(self, stimuli, segments):
        parent_proba = super().get_probabilities(stimuli, segments)

        if self._X:
            self._clf.fit(self._X, self._y)
            joblib.dump(self._clf, str(self.filename))
            self._X, self._y = [], []

        probs = {}
        for stimulus, x in average_segments(stimuli, segments).items():
            probs[stimulus] = self._clf.predict_proba([x])[0, 1]
        return probs