from bredlbot.config import BredlBase
from socket import socket, error as ChatConnectionError


class ChatSocket(BredlBase):

    class _Const:
        CHUNK_SIZE = 1024
        UTF = 'utf-8'
        LINE_END = '\r\n'
        TWITCH_CAPABILITIES = ('membership', 'tags', 'commands')

    def __init__(self, channel):
        super().__init__()
        self._socket = socket()
        self._channel = channel.lower()
        self._buffer = ''

    def _enable_twitch_irc_capabilities(self):
        req = 'CAP REQ :twitch.tv/{}'
        for cap in ChatSocket._Const.TWITCH_CAPABILITIES:
            self._send_utf(req.format(cap))

    def join(self, twitch_irc):
        self._socket.connect((self._host, self._port))
        self._send_utf("PASS {}{}".format(self._pass, ChatSocket._Const.LINE_END))
        self._send_utf("NICK {}{}".format(self._nick, ChatSocket._Const.LINE_END))
        self._send_utf("JOIN #{}{}".format(self._channel, ChatSocket._Const.LINE_END))
        if twitch_irc:
            self._enable_twitch_irc_capabilities()

    def _send_utf(self, message):
        self._socket.send(message.encode(ChatSocket._Const.UTF))

    def _recv_utf(self):
        return self._socket.recv(ChatSocket._Const.CHUNK_SIZE).decode(ChatSocket._Const.UTF)

    def _recv_messages(self):
        self._buffer += self._recv_utf()
        messages = self._buffer.split(ChatSocket._Const.LINE_END)
        self._buffer = messages.pop()
        return messages

    def _process_messages(self, messages):
        for message in messages:
            if message[0] == 'PING':
                print("We ponged!")
                self._send_utf('PONG :{}'.format(message[-1]))
                continue
            print(message)

    @staticmethod
    def _format_message(message):
        temp = message.split(':')
        return temp

    def listen(self):
        try:
            while True:
                self._process_messages(self._recv_messages())
        except Exception as e:
            self._logger.log(e)
