from bredlbot.chatsocket import ChatSocket, ChatConnectionError
from bredlbot.logger import Logger


class BredlBot:
    def __init__(self, channel, directory='logs/errors/'):
        self._chat = ChatSocket(channel)
        self._error_logger = Logger(directory)

    def run(self, twitch_irc=True):
        try:
            self._chat.join(twitch_irc=twitch_irc)
            self._chat.listen()
        except ChatConnectionError as error:
            self._error_logger.log(error)


if __name__ == '__main__':
    bot = BredlBot("dansgaming")
    bot.run()
