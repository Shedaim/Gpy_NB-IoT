import sys
from machine import SD
import os

CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10
NOTSET   = 0

_level_dict = {
    CRITICAL: "CRIT",
    ERROR: "ERROR",
    WARNING: "WARN",
    INFO: "INFO",
    DEBUG: "DEBUG",
}

_stream = sys.stderr


class Logger:

    level = NOTSET

    def __init__(self, name, sd):
        self.name = name
        self.sd = sd

    def _level_str(self, level):
        l = _level_dict.get(level)
        if l is not None:
            return l
        return "%s" % level

    def setLevel(self, level):
        self.level = level

    def isEnabledFor(self, level):
        return level >= (self.level or _level)

    def log(self, level, msg, *args):
        if level >= (self.level or _level):
            _stream.write("%s: %s: " % (self._level_str(level), self.name))
            if not args:
                print(msg, file=_stream)
                if self.sd is not None:
                    self.save_to_file(level, msg, _stream)
            else:
                print(msg % args, file=_stream)
                if self.sd is not None:
                    self.save_to_file(level, msg, _stream)

    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)

    def exc(self, e, msg, *args):
        self.log(ERROR, msg, *args)
        sys.print_exception(e, _stream)

    def exception(self, msg, *args):
        self.exc(sys.exc_info()[1], msg, *args)

    def save_to_file(self, level, msg, _stream):
        try:
            with open('/sd/logs.log','a') as file:
                s = self._level_str(level) + ': ' + self.name + ': ' + msg + '\n'
                file.write(s)
        except OSError as e:
            sys.print_exception(e, _stream)


_level = INFO
_loggers = {}
_sdcard = None


def getLogger(name):
    global _sdcard
    if name in _loggers:
        return _loggers[name]
    if _sdcard is None:
        try:
            _sdcard = SD()
            os.mount(_sdcard, '/sd')
        except OSError:
            _sdcard = None
            print("SD card not found. Logs will not be saved to file.")
    l = Logger(name, _sdcard)
    _loggers[name] = l
    return l

def info(msg, *args):
    getLogger(None).info(msg, *args)

def debug(msg, *args):
    getLogger(None).debug(msg, *args)

def basicConfig(level=INFO, filename=None, stream=None, format=None):
    global _level, _stream
    _level = level
    if stream:
        _stream = stream
    if filename is not None:
        print("logging.basicConfig: filename arg is not supported")
    if format is not None:
        print("logging.basicConfig: format arg is not supported")
