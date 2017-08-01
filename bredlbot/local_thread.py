from bredlbot.job_thread import StoppableThread
from datetime import datetime
import os
import codecs


class LocalLoggerThread(StoppableThread):
    def __init__(self, channel, debug=False):
        super().__init__(debug)
        self._channel = channel.lower()
        self._messages = []
        self._create_db_entry()

    def _create_db_entry(self):
        if not os.path.exists(self._channel):
            os.makedirs(self._channel)

    def log(self, message, meta_data):
        self._messages.append([message, meta_data])

    def _commit_messages(self):
        date = datetime.utcnow().strftime('%Y_%m_%d')
        with codecs.open('{}/{}.txt'.format(self._channel, date), 'a', 'utf-8-sig') as log:
            for m in self._messages:
                log.write(str(m)+'\r\n')
        self._messages = []

    def run(self):
        while True:
            while self._messages:
                self._commit_messages()
            if self._break:
                if self._debug:
                    print(' Logger culled.')
                break