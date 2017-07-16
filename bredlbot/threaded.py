from threading import Thread, Event
from time import time


CHUNK_SIZE = 1024


class Counter:
    def __init__(self):
        self._count = 0

    def reset(self):
        self._count = 0

    def __call__(self):
        temp = self._count
        self._count += 1
        return temp


class RecvThread(Thread):
    def __init__(self, socket, channel):
        super().__init__()
        self._counter = Counter()
        self._socket = socket
        self._channel = channel
        self._buffer = ''
        self.messages = []
        self.event = Event()

    def _recv_utf(self):
        return self._socket.recv(CHUNK_SIZE).decode('utf-8')

    def _recv_messages(self):
        self._buffer += self._recv_utf()
        messages = self._buffer.split('\r\n')
        self._buffer = messages.pop()
        self.event.wait()
        self.messages.append((self._counter(), messages))

    def run(self):
        while True:
            self._recv_messages()


class SendThread(Thread):
    def __init__(self, socket, channel, twitch_irc):
        super().__init__()
        self._socket = socket
        self._channel = channel
        self._start = None
        self._count = 0
        self._message_limit = 20
        self.send_buffer = []
        self._twitch_irc = twitch_irc
        self.event = Event()

    def _send_utf(self, message):
        self._socket.send('{}\r\n'.format(message).encode('utf-8'))
        self._count += 1

    def _send_privmsg(self, message):
        self._send_utf("PRIVMSG #{} :{}".format(self._channel, message))

    def _ban_user(self, user, reason, duration=''):
        self._send_privmsg('.timeout {} {} {}'.format(user, reason, duration))

    def _is_valid_period(self):
        curr_time = time()
        if not self._start or curr_time - self._start >= 30:
            self._start = curr_time
            self._count = 0
        return self._count < self._message_limit

    def _send_message(self, message):
        if 'PONG' in message:
            self._send_utf(message)
        else:
            self._send_privmsg(message)

    def _process_send_buffer(self):
        while self.send_buffer:
            if self._is_valid_period():
                self.event.wait()
                self._send_message(self.send_buffer.pop(0))

    def run(self):
        while True:
            self._process_send_buffer()
