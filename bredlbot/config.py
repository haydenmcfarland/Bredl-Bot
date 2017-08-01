class BredlConfError(Exception):
    pass


class BredlBase:
    """
    'config.conf' file format:
        irc.twitch.tv
        6667
        BOT_NAME
        oauth:OAUTH_TOKEN
    """
    def __init__(self):
        try:
            with open('config.conf') as conf:
                params = conf.read().split()
                self._host = params[0]
                self._port = int(params[1])
                self._nick = params[2]
                self._pass = params[3]
                self._cid = params[-1]
        except:
            raise BredlConfError
