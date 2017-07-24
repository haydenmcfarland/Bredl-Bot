from bredlbot.config import BredlBase
from bredlbot.threaded import RecvThread, SendThread, LoggerThread
import bredlbot.commands as commands
from socket import socket, error as ChatConnectionError
import re

# TWITCH SPECIFIC
TWITCH_CAPABILITIES = ('membership', 'tags', 'commands')

# REGEX EXPRESSIONS
RE_CHAT = re.compile('(.*):(.+)!.+@.+.tmi.twitch.tv (.+) #.+ :(.+)')
RE_MOTD = re.compile('(.*):tmi.twitch.tv 376 (\S+) :(.+)')
RE_PING = re.compile('PING :tmi.twitch.tv')

# LOCAL CONSTANTS
COMMAND = 3
TEXT = 4
USER = 2
TWITCH = 1


class ChatSocket(BredlBase):
    def __init__(self, channel, log_only, twitch_irc):
        super().__init__()
        self._socket = socket()
        self._channel = channel.lower()
        self._recv_thread = RecvThread(self._socket, self._channel)
        self._log_only = log_only
        self._send_thread = SendThread(self._socket, self._channel, twitch_irc)
        self._chat_logger = LoggerThread(self._channel)
        self._twitch_irc = twitch_irc
        self._debug = False


    def _send_utf(self, message):
        self._socket.send('{}\r\n'.format(message).encode('utf-8'))

    def _enable_twitch_irc_capabilities(self):
        for cap in TWITCH_CAPABILITIES:
            self._send_utf('CAP REQ :twitch.tv/{}'.format(cap))

    def _join(self):
        self._socket.connect((self._host, self._port))
        self._send_utf("PASS {}".format(self._pass))
        self._send_utf("NICK {}".format(self._nick))
        self._send_utf("JOIN #{}".format(self._channel))
        if self._twitch_irc:
            self._enable_twitch_irc_capabilities()

    def _append_send_buffer(self, message):
        self._send_thread.event.clear()
        self._send_thread.send_buffer.append(message)
        self._send_thread.event.set()

    def _generate_meta_data(self, twitch_params):
        valid = ['color', 'display-name', 'mod', 'emotes', 'sent-ts', 'subscriber']
        return dict([j for j in [i.split('=') for i in twitch_params.split(';')] if j[-1] != '' and j[0] in valid])

    def _process_messages(self, messages):
        for message in messages:
            if self._debug:
                print(message)

            if re.match(RE_PING, message):
                self._send_thread.event.clear()
                self._send_thread.send_buffer.append('PONG :tmi.twitch.tv')
                self._send_thread.event.set()
            else:
                r = re.match(RE_CHAT, message)
                if r:
                    if r.group(COMMAND) == "PRIVMSG":
                        chat_msg = '{}: {}'.format(r.group(USER), r.group(TEXT))
                        meta_data = self._generate_meta_data(r.group(TWITCH))
                        self._chat_logger.log(chat_msg, meta_data)
                        if not self._log_only:
                            if '!hello' in r.group(TEXT):
                                self._append_send_buffer(commands.hello(r.group(USER)))
                            elif '!' == r.group(TEXT):
                                self._append_send_buffer(commands.solid())
                            elif '!dev' in r.group(TEXT):
                                self._append_send_buffer(commands.dev())
                            elif '!roll' == r.group(TEXT):
                                self._append_send_buffer(commands.roll(r.group(USER)))

    def run(self):
        self._join()
        self._chat_logger.start()
        self._send_thread.start()
        self._recv_thread.start()
        while True:
            self._recv_thread.event.clear()
            messages_list = self._recv_thread.messages
            self._recv_thread.messages = []
            self._recv_thread.event.set()
            if messages_list:
                for messages in messages_list:
                    self._process_messages(messages[-1])
