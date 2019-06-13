import asyncio
import json
import logging
from struct import Struct


LENGTH_STRUCT = Struct('N')
logger = logging.getLogger(__name__)


class InteractionClient:
    def __init__(self, reader, writer):
        self._reader, self._writer = reader, writer

    def stop(self):
        if self._writer is not None:
            self._writer.close()

    async def request_config(self):
        return await self._request({'action': 'request_config'})

    async def signal(self, signal_name, *args):
        await self._send_message({'action': 'signal', 'signal': signal_name, 'args': args})

    async def _send_message(self, message):
        message_json = json.dumps(message)
        logger.debug("Message sent: %s", message_json)
        payload = message_json.encode('utf-8')
        self._writer.write(LENGTH_STRUCT.pack(len(payload)) + payload)
        await self._writer.drain()

    async def _read_message(self):
        length = LENGTH_STRUCT.unpack(await self._reader.read(LENGTH_STRUCT.size))[0]
        payload = await self._reader.read(length)
        return json.loads(payload.decode('utf-8'))

    async def _request(self, message):
        await self._send_message(message)
        return await self._read_message()


async def connect_to_app(port) -> InteractionClient:
    reader, writer = await asyncio.open_connection('localhost', port)
    return InteractionClient(reader, writer)
