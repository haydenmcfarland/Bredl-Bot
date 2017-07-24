from bredlbot.chatsocket import ChatSocket, ChatConnectionError


class BredlBot:
    def __init__(self, channel, log_only=False, twitch_irc=True):
        self._chat = ChatSocket(channel, log_only, twitch_irc)

    def run(self):
        try:
            self._chat.run()
        except ChatConnectionError as e:
            print(e)


if __name__ == '__main__':
    BredlBot('itmeJP', log_only=False, twitch_irc=True).run()
