import errno
import os
from logging.handlers import TimedRotatingFileHandler


def mkdir_p(path):
    try:
        os.makedirs(path, exist_ok=True)  # Python>3.2
    except TypeError:
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                print(exc)


class MakeFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='h', interval=1, backup_count=0, encoding=None, delay=False, utc=False,
                 at_time=None):
        mkdir_p(os.path.dirname(filename))
        TimedRotatingFileHandler.__init__(self, filename, when, interval, backup_count, encoding, delay, utc, at_time)
