import asyncio
import logging
from struct import Struct
from time import time


logger = logging.getLogger(__name__)


class CyKitClient:
    def __init__(self, reader, writer, channels=14, sample_rate=128):
        self.sample_rate = sample_rate
        self._reader, self._writer = reader, writer
        self._struct = Struct('>' + 'f' * channels)

    def stop(self):
        if self._writer is not None:
            self._writer.close()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._reader.at_eof():
            raise ConnectionError("No more data from peer")
        data = await self._reader.readexactly(self._struct.size)
        if not data:
            raise ConnectionError("No more data from peer")

        return self._struct.unpack(data)

    async def _initialize(self, good_packet_threshold=64):
        last_time = time()
        good_packets = 0

        while good_packets < good_packet_threshold:
            await self._reader.readexactly(self._struct.size)

            cur_time = time()
            delta = cur_time - last_time
            if delta > (1.0 / self.sample_rate) / 2:
                good_packets += 1
                logger.debug("Good packet: %.4f ms", delta * 1000.0)
            else:
                logger.debug("Bad packet: %.4f ms", delta * 1000.0)

            last_time = cur_time

        return self


async def connect_to_cykit(ip, port, timeout=3) -> CyKitClient:
    fut = asyncio.open_connection(ip, port)
    reader, writer = await asyncio.wait_for(fut, timeout)

    client = CyKitClient(reader, writer)
    return await client._initialize()
