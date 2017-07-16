from bredlbot.config import BredlBase
from bredlbot.logger import Logger
from bredlbot.threaded import RecvThread, SendThread
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


class ChatSocket(BredlBase):
    def __init__(self, channel, twitch_irc):
        super().__init__()
        self._socket = socket()
        self._channel = channel.lower()
        self._recv_thread = RecvThread(self._socket, self._channel)
        self._send_thread = SendThread(self._socket, self._channel, twitch_irc)
        self._chat_logger = Logger('logs/chat/{}/'.format(self._channel))
        self._twitch_irc = twitch_irc

    def _send_utf(self, message):
        self._socket.send('{}\r\n'.format(message).encode('utf-8'))

    def _enable_twitch_irc_capabilities(self):
        for cap in TWITCH_CAPABILITIES:
            self._send_utf('CAP REQ :twitch.tv/{}'.format(cap))
        self._twitch_irc = True

    def _join(self):
        self._socket.connect((self._host, self._port))
        self._send_utf("PASS {}".format(self._pass))
        self._send_utf("NICK {}".format(self._nick))
        self._send_utf("JOIN #{}".format(self._channel))
        if self._twitch_irc:
            self._enable_twitch_irc_capabilities()

    def _process_messages(self, messages):
        for message in messages:
            if re.match(RE_PING, message):
                self._send_thread.send_buffer.append('PONG :tmi.twitch.tv')
            else:
                r = re.match(RE_CHAT, message)
                if r:
                    if r.group(COMMAND) == "PRIVMSG":
                        chat_msg = '{}: {}'.format(r.group(USER), r.group(TEXT))
                        self._chat_logger.log(chat_msg)
                        if '!hello' in r.group(TEXT):
                            send_msg = 'Hey {}! Right now all I can do is say hi and create logs, \
                            but stay tuned for more features.'.format(r.group(USER))
                            self._send_thread.send_buffer.append(send_msg)

    def run(self):
        self._join()
        self._send_thread.start()
        self._recv_thread.start()
        while True:
            messages_list = self._recv_thread.messages
            self._recv_thread.messages = []
            if messages_list:
                for messages in messages_list:
                    self._process_messages(messages)
