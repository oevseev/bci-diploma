import asyncio
import logging
import signal
from argparse import ArgumentParser

from model import ConcretePreprocessingStrategy, LDAModel
from realtime import Session


def main():
    logging.basicConfig(level=logging.WARNING)

    args = parse_args()
    preproc_strategy = ConcretePreprocessingStrategy()
    model = LDAModel()
    session = Session(args, preproc_strategy, model)

    loop = asyncio.get_event_loop()

    try:
        loop.add_signal_handler(signal.SIGINT, session.stop)
        loop.add_signal_handler(signal.SIGTERM, session.stop)
    except NotImplementedError:
        pass

    try:
        loop.run_until_complete(session.run())
    except KeyboardInterrupt:
        session.stop()
    finally:
        loop.close()


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('cykit_address', help='IP address CyKit is located at')
    parser.add_argument('cykit_port', help='Port CyKit server listens on', type=int)
    parser.add_argument('interaction_port', help='Port interaction server listens on', type=int)

    parser.add_argument('tti', help='Target-to-target interval',
                        type=float, nargs='?', default=0.3)
    parser.add_argument('num_repetitions', help='Number of repetitions of a stimulus',
                        type=int, nargs='?', default=5)
    parser.add_argument('highlight_time', help='Highlight time in training mode',
                        type=float, nargs='?', default=5.0)
    parser.add_argument('segment_duration', help='Segment duration in samples (after preprocessing)',
                        type=int, nargs='?', default=128)
    parser.add_argument('delay_between_iters', help='Delay between iterations',
                        type=float, nargs='?', default=1.0)

    return parser.parse_args()


if __name__ == '__main__':
    main()
