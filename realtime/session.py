import asyncio
import random
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor

from model import PreprocessingStrategy, Model
from realtime.acquisition import connect_to_cykit
from realtime.app_interaction import connect_to_app
from realtime.preprocessing import Preproc

LETTERS = ['ABCDEF', 'GHIJKL', 'MNOPQR', 'STUVWX', 'YZ0123', '456789']
NUM_MOUSE_CLASSES = 5


class Session:
    def __init__(self, args: Namespace, preprocessing_strategy: PreprocessingStrategy, model: Model):
        self.preprocessing_strategy = preprocessing_strategy
        self.model = model
        self.args = args
        self._cykit_client = None
        self._interaction_client = None
        self._preproc = Preproc(self.preprocessing_strategy)
        self._executor = None
        self._wait_for_executor()

    async def run(self):
        try:
            self._cykit_client = await connect_to_cykit(self.args.cykit_address, self.args.cykit_port)
            self._interaction_client = await connect_to_app(self.args.interaction_port)
            await asyncio.gather(
                self._preproc.run(self._cykit_client, self._executor),
                self._run_session())

        finally:
            self.stop()

    def stop(self):
        if self._cykit_client is not None:
            self._cykit_client.stop()
        if self._interaction_client is not None:
            self._interaction_client.stop()

    async def _run_session(self):
        while True:
            meta = await self._interaction_client.request_config()
            if meta['mode'] == 'keyboard':
                await self._run_keyboard_iteration(meta['train'])
            elif meta['mode'] == 'mouse':
                await self._run_mouse_iteration(meta['train'])
            else:
                raise RuntimeError("Invalid mode")

    # TODO: Extract common code from this and _run_single_class_iteration
    async def _run_keyboard_iteration(self, train=False):
        target_row, target_col = None, None
        if train:
            target_row = random.randrange(0, len(LETTERS))
            target_col = random.randrange(0, len(LETTERS[0]))
            target_letter = LETTERS[target_row][target_col]
            asyncio.create_task(self._interaction_client.signal('keyboard_highlight_letter', target_letter))
            await asyncio.sleep(self.args.highlight_time)

        stimuli = []
        for _ in range(self.args.num_repetitions):
            for i in range(len(LETTERS)):
                stimuli.append(('row', i))
            for i in range(len(LETTERS[0])):
                stimuli.append(('col', i))
        random.shuffle(stimuli)

        futures = []
        for stimulus_type, idx in stimuli:
            if stimulus_type == 'row':
                asyncio.create_task(self._interaction_client.signal('keyboard_flash_row', idx))
            elif stimulus_type == 'col':
                asyncio.create_task(self._interaction_client.signal('keyboard_flash_col', idx))
            fut = asyncio.create_task(self._preproc.get_segment(duration=self.args.segment_duration))
            futures.append(fut)
            await asyncio.sleep(self.args.tti)

        segments = await asyncio.gather(*futures)
        if train:
            target = [('row', target_row), ('col', target_col)]
            asyncio.create_task(self._train_iteration(stimuli, segments, target))
        else:
            probs = await self._get_probabilities(stimuli, segments)
            relevant_row = max(filter(lambda x: x[0] == 'row', probs), key=probs.get)[1]
            relevant_col = max(filter(lambda x: x[0] == 'col', probs), key=probs.get)[1]
            relevant_letter = LETTERS[relevant_row][relevant_col]
            asyncio.create_task(self._interaction_client.signal('keyboard_select_letter', relevant_letter))

        # During this time, any extra unprocessed packets will be ignored to avoid latency
        await asyncio.sleep(self.args.delay_between_iters)

    async def _run_mouse_iteration(self, train=False):
        target_class = None
        if train:
            target_class = random.randrange(0, NUM_MOUSE_CLASSES)
            asyncio.create_task(self._interaction_client.signal('mouse_highlight_class', target_class))
            await asyncio.sleep(self.args.highlight_time)

        stimuli = list(range(NUM_MOUSE_CLASSES)) * self.args.num_repetitions
        random.shuffle(stimuli)

        futures = []
        for idx in stimuli:
            asyncio.create_task(self._interaction_client.signal('mouse_flash_class', idx))
            fut = asyncio.create_task(self._preproc.get_segment(duration=self.args.segment_duration))
            futures.append(fut)
            await asyncio.sleep(self.args.tti)

        segments = await asyncio.gather(*futures)
        if train:
            asyncio.create_task(self._train_iteration(stimuli, segments, [target_class]))
        else:
            probs = await self._get_probabilities(stimuli, segments)
            relevant_class = max(probs, key=probs.get)
            asyncio.create_task(self._interaction_client.signal('mouse_select_class', relevant_class))

        await asyncio.sleep(self.args.delay_between_iters)

    async def _train_iteration(self, stimuli, segments, target):
        self._wait_for_executor()
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self.model.train_iteration, stimuli, segments, target)

    async def _get_probabilities(self, stimuli, segments):
        self._wait_for_executor()
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self.model.get_probabilities, stimuli, segments)

    def _wait_for_executor(self):
        if self._executor is not None:
            self._executor.shutdown(wait=True)
        self._executor = ThreadPoolExecutor()
