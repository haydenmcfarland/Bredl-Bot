from datetime import datetime
from os.path import exists, abspath
from os import makedirs


class Logger:
    def __init__(self, directory):
        self._dir = abspath(directory)

    def log(self, obj_or_message):

        if not exists(self._dir):
            makedirs(self._dir)

        with open('{}/{}.txt'.format(self._dir, datetime.now().strftime('%Y_%m_%d')), 'a') as logs:
            log_template = 'TIME: [{}] MSG: [{}]\r\n'
            logs.write(log_template.format(datetime.now().strftime('%H:%M:%S'), obj_or_message))
