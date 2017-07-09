from bredlbot.config import BredlBase
from bredlbot.logger import Logger
from socket import socket, error as ChatConnectionError
import re


class ChatSocket(BredlBase):

    class _Const:
        CHUNK_SIZE = 1024
        UTF = 'utf-8'
        TWITCH_CAPABILITIES = ('membership', 'tags', 'commands')
        RE_IRC_PATTERN = re.compile('(.+)!.+@.+.tmi.twitch.tv (.+) #.+')

    def __init__(self, channel):
        super().__init__()
        self._socket = socket()
        self._channel = channel.lower()
        self._buffer = ''
        self._chat_logger = Logger('logs/chat/')
        self._twitch_irc = False

    def _enable_twitch_irc_capabilities(self):
        for cap in ChatSocket._Const.TWITCH_CAPABILITIES:
            self._send_utf('CAP REQ :twitch.tv/{}'.format(cap))
        self._twitch_irc = True

    def _send_utf(self, message):
        self._socket.send('{}\r\n'.format(message).encode(ChatSocket._Const.UTF))

    def _send_privmsg(self, message):
        self._send_utf("PRIVMSG #{} :{}".format(self._channel, message))

    def _recv_utf(self):
        return self._socket.recv(ChatSocket._Const.CHUNK_SIZE).decode(ChatSocket._Const.UTF)

    def _recv_messages(self):
        self._buffer += self._recv_utf()
        messages = self._buffer.split('\r\n')
        self._buffer = messages.pop()
        return messages

    def _process_messages(self, messages):
        for message in messages:
            message = [m.strip() for m in message.split(':')]
            if message[0] == 'PING':
                self._send_utf('PONG :{}'.format(message[-1]))
                continue
            elif self._twitch_irc:
                m = re.match(ChatSocket._Const.RE_IRC_PATTERN, message[1])
                if m:
                    if m.group(1) == '8by3':
                        self._send_privmsg("({}) said: {} danGasm".format(m.group(1), message[-1]))
                    #self._chat_logger.log('{} said {}'.format(m.group(1), message[-1]))
                    print(message)
            else:
                continue

    def join(self, twitch_irc):
        self._socket.connect((self._host, self._port))
        self._send_utf("PASS {}".format(self._pass))
        self._send_utf("NICK {}".format(self._nick))
        self._send_utf("JOIN #{}".format(self._channel))
        if twitch_irc:
            self._enable_twitch_irc_capabilities()

    def listen(self):
        while True:
            messages = self._recv_messages()
            self._process_messages(messages)
