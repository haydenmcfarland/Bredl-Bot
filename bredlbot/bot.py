from bredlbot.chat_thread import ChatThread
import time


class BredlThread(ChatThread):
    pass


if __name__ == '__main__':
    x = BredlThread('BredlBot', log_only=False, twitch_irc=True, debug=True)
    x.start()
    time.sleep(5)
    x.stop()