import asyncio
from concurrent.futures.thread import ThreadPoolExecutor

from model import PreprocessingStrategy


class Preproc:
    def __init__(self, preprocessing_strategy: PreprocessingStrategy):
        self.preprocessing_strategy = preprocessing_strategy
        self._segments = set()
        self._counter = 0

    async def run(self, cykit_client, executor=None):
        batch = []
        batch_start = self._counter

        async for sample in cykit_client:
            batch.append(sample)
            self._counter += 1
            if len(batch) < self.preprocessing_strategy.batch_size:
                continue

            with ThreadPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                preprocessed_batch = await loop.run_in_executor(
                    executor, self.preprocessing_strategy.preprocess_batch, batch)
            for segment in self._segments:
                segment.append_batch(preprocessed_batch, batch_start)

            batch = []
            batch_start = self._counter

    async def get_segment(self, duration=128):
        segment = PartialSegment(duration, self._counter)

        self._segments.add(segment)
        data = await segment.get_complete_data()
        self._segments.discard(segment)

        return segment.start, data


class PartialSegment:
    def __init__(self, duration, start):
        self.duration = duration
        self.start = start

        self._first_batch_start = None
        self._samples = []
        self._queue = asyncio.Queue()

    async def get_complete_data(self):
        return await self._queue.get()

    def append_batch(self, batch, batch_start):
        self._samples += batch

        if self._first_batch_start is None:
            self._first_batch_start = batch_start
        offset = self.start - self._first_batch_start
        if len(self._samples) - offset < self.duration:
            return

        self._samples = self._samples[offset:(offset + self.duration)]
        self._queue.put_nowait(self._samples)
