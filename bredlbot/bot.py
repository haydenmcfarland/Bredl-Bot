from bredlbot.chat_thread import ChatThread


class BredlThread(ChatThread):
    pass

if __name__ == '__main__':
    x = BredlThread('8by3', log_only=False, twitch_irc=True, debug=True, local=True)
    x.run()