from bredlbot.chatsocket import ChatSocket, ChatConnectionError
from bredlbot.logger import Logger


class BredlBot:
    def __init__(self, channel, directory='logs/errors/', twitch_irc=True):
        self._chat = ChatSocket(channel, twitch_irc)
        self._error_logger = Logger(directory)

    def run(self):
        try:
            self._chat.run()
        except ChatConnectionError as error:
            self._error_logger.log(error)


if __name__ == '__main__':
    BredlBot('BredlBot', twitch_irc=False).run()
