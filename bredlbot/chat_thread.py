from bredlbot.config import BredlBase
from bredlbot.job_thread import RecvThread, SendThread, LoggerThread, StoppableThread
from bredlbot.local_thread import LocalLoggerThread
from bredlbot import whispers
import bredlbot.commands as commands
from socket import socket, SHUT_WR
from twitchpy.api import TwitchAPI
from requests import HTTPError
from datetime import datetime
import re

# TWITCH
TWITCH_CAPABILITIES = ('membership', 'tags', 'commands')

# REGEX
RE_CHAT = re.compile('(.*):(.+)!.+@.+.tmi.twitch.tv (.+) #?.+ :(.+)')
RE_MOD = re.compile('.+:tmi.twitch.tv NOTICE #.+ :(.+)')
RE_MOTD = re.compile('(.*):tmi.twitch.tv 376 (\S+) :(.+)')
RE_PING = re.compile('PING :tmi.twitch.tv')

# CONSTANTS
COMMAND = 3
TEXT = 4
USER = 2
TWITCH = 1
MOD = 0


class ChatThread(StoppableThread, BredlBase):
    def __init__(self, channel, log_only, twitch_irc, oauth_token=None, local=False, debug=False):
        StoppableThread.__init__(self, debug=debug)
        BredlBase.__init__(self)
        self._socket = socket()
        self._channel = channel.lower()
        self._log_only = log_only
        self._api_caller = TwitchAPI(self._cid, oauth_token)
        self._threads = dict()
        if local:
            self._threads['Logger'] = LocalLoggerThread(self._channel, debug=debug)
        else:
            self._threads['Logger'] = LoggerThread(self._channel, debug=debug)
        self._threads['Send'] = SendThread(self._socket, self._channel, twitch_irc, debug=debug)
        self._threads['Recv'] = RecvThread(self._socket, self._channel, debug=debug)
        self._twitch_irc = twitch_irc
        self._is_mod = False
        self.oauth_expired = False

    @staticmethod
    def _generate_meta_data(twitch_params):
        valid = ['color', 'display-name', 'mod', 'emotes', 'sent-ts', 'subscriber']
        return dict([j for j in [i.split('=') for i in twitch_params.split(';')] if j[-1] != '' and j[0] in valid])

    def _send_utf(self, message):
        self._socket.send('{}\r\n'.format(message).encode('utf-8'))

    def _enable_twitch_irc_capabilities(self):
        for c in TWITCH_CAPABILITIES:
            self._send_utf('CAP REQ :twitch.tv/{}'.format(c))

    def _join_twitch_chat(self):
        self._socket.connect((self._host, self._port))
        self._send_utf("PASS {}".format(self._pass))
        self._send_utf("NICK {}".format(self._nick))
        self._send_utf("JOIN #{}".format(self._channel))
        if self._twitch_irc:
            self._enable_twitch_irc_capabilities()
        self._append_send_buffer("/mods")

    def _start_threads(self):
        for t in self._threads:
            self._threads[t].start()

    def _stop_threads(self):
        for t in self._threads:
            self._threads[t].stop()

    def _join_threads(self):
        for t in self._threads:
            self._threads[t].join()

    def _append_send_buffer(self, message):
        self._threads['Send'].event.clear()
        self._threads['Send'].send_buffer.append(message)
        self._threads['Send'].event.set()

    def _pop_recv_buffer(self):
        self._threads['Recv'].event.clear()
        messages_list = self._threads['Recv'].messages
        self._threads['Recv'].messages = []
        self._threads['Recv'].event.set()
        return messages_list

    def _process_messages(self, messages):
        for message in messages:
            if self._debug:
                print(message)

            if re.match(RE_PING, message):
                self._append_send_buffer('PONG :tmi.twitch.tv')
            else:
                r = re.match(RE_MOD, message)
                if r:
                    self._is_mod = self._nick in (c.strip() for c in r.group(MOD).split(':')[-1].split(','))
                    msg = whispers.w_mod_status(self._channel, self._is_mod)
                    self._append_send_buffer(msg)
                r = re.match(RE_CHAT, message)
                if r:
                    if r.group(COMMAND) == "WHISPER":
                        if r.group(USER) == self._channel:
                            if r.group(TEXT) == '!mod':
                                self._append_send_buffer('/mods')
                    elif r.group(COMMAND) == "PRIVMSG":
                        chat_msg = '{}: {}'.format(r.group(USER), r.group(TEXT))
                        meta_data = ChatThread._generate_meta_data(r.group(TWITCH))
                        self._threads['Logger'].log(chat_msg, meta_data)
                        if not self._log_only:
                            if '!hello' == r.group(TEXT):
                                self._append_send_buffer(commands.hello(r.group(USER)))
                            elif '!' == r.group(TEXT):
                                self._append_send_buffer(commands.solid())
                            elif '!dev' == r.group(TEXT):
                                self._append_send_buffer(commands.dev())
                            elif '!roll' == r.group(TEXT):
                                self._append_send_buffer(commands.roll(r.group(USER)))
                            elif not self.oauth_expired and '!uptime' == r.group(TEXT):
                                try:
                                    _id = self._api_caller.users.get_user()['_id']
                                    stream = self._api_caller.streams.get_stream_by_user(channel_id=_id)
                                    d = None
                                    if 'stream' in stream:
                                        if 'created_at' in stream['stream']:
                                            print(stream['stream'])
                                            _created_at = stream['stream']['created_at']
                                            _created_at = datetime.strptime(_created_at, '%Y-%m-%dT%H:%M:%SZ')
                                            d = datetime.utcnow() - _created_at
                                    self._append_send_buffer(commands.uptime(d))
                                except HTTPError:
                                    self.oauth_expired = True

    def run(self):
        self._join_twitch_chat()
        self._start_threads()
        while True:
            if self._break:
                self._socket.shutdown(SHUT_WR)
                self._stop_threads()
                if self._debug:
                    print('Terminating {} bot thread.'.format(self._channel))
                break
            messages_list = self._pop_recv_buffer()
            if messages_list:
                for messages in messages_list:
                    self._process_messages(messages[-1])
        self._join_threads()
        self._socket.close()
