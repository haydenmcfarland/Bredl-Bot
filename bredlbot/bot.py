from bredlbot.chatsocket import ChatSocket, ChatConnectionError


class BredlBot:
    def __init__(self, channel, twitch_irc=True):
        self._chat = ChatSocket(channel, twitch_irc)

    def run(self):
        try:
            self._chat.run()
        except ChatConnectionError as error:
            print('Failed')


if __name__ == '__main__':
    BredlBot('BredlBot', twitch_irc=False).run()
