from threading import Thread, Event
from time import time, sleep
from dynopy.dynopy import DynoPy
from dynopy.helper import dict_gen
from datetime import datetime
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


class StoppableThread(Thread):
    def __init__(self, debug=False):
        super().__init__()
        self._break = False
        self._debug = debug

    def stop(self):
        self._break = True


class RecvThread(StoppableThread):
    def __init__(self, socket, channel, debug=False):
        super().__init__(debug)
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
            if self._break:
                if self._debug:
                    print(' Recv buffer culled.')
                break
            self._recv_messages()


class SendThread(StoppableThread):
    def __init__(self, socket, channel, twitch_irc, debug=False):
        super().__init__(debug)
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
            if self._break:
                if self._debug:
                    print(' Send buffer culled.')
                break
            self._process_send_buffer()


WAIT_TIME_FOR_MESSAGES = 300


class LoggerThread(StoppableThread):
    def __init__(self, channel, debug=False):
        super().__init__(debug)
        self._channel = channel.lower()
        self._messages = []
        self._event = Event()
        self._aws = DynoPy(debug=True)
        self._create_db_entry()
        self._add_today_entry()

    def _add_today_entry(self):
        date = datetime.utcnow().strftime('%Y_%m_%d')
        u = 'SET logs.#d = :l, log_dates = list_append(log_dates, :d)'
        n = {'#d': date}
        v = {':l': ['$'], ':d': [date]}
        c = 'attribute_not_exists(logs.#d)'
        response = self._aws.update('Chat', dict_gen(channel=self._channel), u, n, v, c, 'NONE')
        if self._debug:
            print(response)

    def _create_db_entry(self):
        date = datetime.utcnow().strftime('%Y_%m_%d')
        c = 'attribute_not_exists(logs)'
        item = dict_gen(channel=self._channel, logs={date: ['$begin']}, log_dates=[date])
        response = self._aws.put('Chat', item=item, condition_expression=c)
        if self._debug:
            print(response)

    def log(self, message, meta_data):
        self._messages.append([message, meta_data])

    def _commit_messages(self):
        date = datetime.utcnow().strftime('%Y_%m_%d')
        u = "SET logs.#d = list_append(logs.#d, :i)"
        n = {'#d': date}
        v = {':i': self._messages}
        c = "attribute_exists(logs.#d)"
        response = self._aws.update('Chat', dict_gen(channel=self._channel), u, n, v, c, 'NONE')
        if self._debug:
            print(response)
        if response['ResponseMetadata']['HTTPStatusCode'] == 400:
            self._add_today_entry()
        elif response['ResponseMetadata']['HTTPStatusCode'] == 200:
            self._messages = []

    def run(self):
        while True:
            sleep(WAIT_TIME_FOR_MESSAGES)
            while self._messages:
                self._commit_messages()
            if self._break:
                if self._debug:
                    print(' Logger culled.')
                break
