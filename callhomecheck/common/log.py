import logging
import sys
import os
import datetime


class baseFormat:
    reset = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strikethrough = '\033[09m'
    invisible = '\033[08m'


class fg(baseFormat):
    black = '\033[30m'
    red = '\033[31m'
    green = '\033[32m'
    orange = '\033[33m'
    blue = '\033[34m'
    purple = '\033[35m'
    cyan = '\033[36m'
    lightgrey = '\033[37m'
    darkgrey = '\033[90m'
    lightred = '\033[91m'
    lightgreen = '\033[92m'
    yellow = '\033[93m'
    lightblue = '\033[94m'
    pink = '\033[95m'
    lightcyan = '\033[96m'


class bg(baseFormat):
    black = '\033[40m'
    red = '\033[41m'
    green = '\033[42m'
    orange = '\033[43m'
    blue = '\033[44m'
    purple = '\033[45m'
    cyan = '\033[46m'
    lightgrey = '\033[47m'


class ColorLevelFormatter(logging.Formatter):
    def format(self, record):
        origMsg = record.msg
        if record.levelno == logging.WARNING:
            record.msg = '%s%s%s' % (fg.yellow, record.msg, fg.reset)
        elif record.levelno == logging.ERROR:
            record.msg = '%s%s%s' % (fg.red, record.msg, fg.reset)
        elif record.levelno == logging.CRITICAL:
            record.msg = '%s%s%s' % (fg.lightred, record.msg, fg.reset)
        newMsg = logging.Formatter.format(self, record)
        record.msg = origMsg
        return newMsg


class LogFileFormatter(logging.Formatter):
    converter = datetime.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s.%03d" % (t, record.msecs)
        return s


def getLogger(name):
    if name == '__main__':
        return logging.getLogger(BaseLoggerName)
    else:
        return logging.getLogger(BaseLoggerName + "." + name)


BaseLoggerName = os.path.splitext(os.path.basename(sys.argv[0]))[0]
logging.addLevelName(logging.CRITICAL, 'CRIT')
logging.addLevelName(logging.WARNING, 'WARN')