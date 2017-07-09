import datetime


class Logger:
    def __init__(self, directory):
        self._dir = directory

    def log(self, obj_or_message):
        with open('{}{}.txt'.format(self._dir, datetime.date), 'a') as logs:
            logs.write('[{}] --- [{}]'.format(obj_or_message, datetime.datetime))
