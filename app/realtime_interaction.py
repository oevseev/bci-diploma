import json
import struct

from PySide2.QtCore import QObject, Signal
from PySide2.QtNetwork import QHostAddress, QTcpServer

LENGTH_STRUCT = struct.Struct('N')


class InteractionServer(QObject):
    keyboard_flash_row = Signal(int)
    keyboard_flash_col = Signal(int)
    keyboard_highlight_letter = Signal(str)
    keyboard_select_letter = Signal(str)
    mouse_flash_class = Signal(int)
    mouse_highlight_class = Signal(int)
    mouse_select_class = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._tcp_server = QTcpServer(self)
        self._tcp_server.listen(QHostAddress('localhost'))
        self._tcp_server.newConnection.connect(self._handle_new_connection)

        self.port = self._tcp_server.serverPort()
        self.train = False

    def _handle_new_connection(self):
        connection = self._tcp_server.nextPendingConnection()
        connection.readyRead.connect(self._handle_ready_read)

    def _handle_ready_read(self):
        socket = self.sender()
        while not socket.atEnd():
            length = LENGTH_STRUCT.unpack(socket.read(LENGTH_STRUCT.size).data())[0]
            payload = socket.read(length).data()
            message = json.loads(payload.decode('utf-8'))
            self._handle_message(socket, message)

    def _send_message(self, socket, message):
        payload = json.dumps(message).encode('utf-8')
        socket.write(LENGTH_STRUCT.pack(len(payload)) + payload)
        socket.flush()

    def _handle_message(self, socket, message):
        if message['action'] == 'request_config':
            self._send_message(socket, {
                'mode': 'keyboard',
                'train': self.train
            })
        elif message['action'] == 'signal':
            signal = getattr(self, message['signal'])
            signal.emit(*message['args'])
