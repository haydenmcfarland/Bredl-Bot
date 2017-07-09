from bredlbot.chatsocket import ChatSocket, ChatConnectionError
from bredlbot.logger import Logger


class BredlBot:
    def __init__(self, channel, directory):
        self._chat = ChatSocket(channel)
        self._logger = Logger(directory)

    def run(self, twitch_irc=False):
        try:
            self._chat.join(twitch_irc=twitch_irc)
        except ChatConnectionError as error:
            self._logger.log(error)
        self._chat.listen()


if __name__ == '__main__':
    bot = BredlBot("GamesDoneQuick", '/logs/')
    bot.run(twitch_irc=True)
