from __future__ import print_function
import os
import subprocess
import signal
from threading import Timer
import logging
import pipes
import time
import shutil
import sys
import datetime


def sourceEnv(sourceFile):
    command = ['bash', '-c', 'source ' + sourceFile + ' && env']
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in proc.stdout:
        (key, _, value) = line.rstrip('\r\n').partition("=")
        os.environ[key] = value
    proc.communicate()


def runCommand(command, timeout_sec):
    finished, stdout, stderr, exitCode = runCommandStdOutErrCode(command, timeout_sec)
    if not finished:
        return None
    return stdout


def runCommandCode(command, timeout_sec):
    finished, stdout, stderr, exitCode = runCommandStdOutErrCode(command, timeout_sec)
    if not finished:
        stdout = None
    return stdout, exitCode


def runCommandStdOutErrCode(command, timeout_sec, useShell=False):
    finished = True
    stdout = ''
    stderr = ''

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=useShell)
    def kill_proc(p):
        p.kill()
    timer = Timer(timeout_sec, kill_proc, [proc])
    try:
        timer.start()
        stdout, stderr = proc.communicate()
    finally:
        timer.cancel()

    if proc.returncode == -signal.SIGKILL:
        finished = False
    return finished, stdout, stderr, proc.returncode


def runRemoteCommandStdOutErrCode(host, command, timeout_sec):
    import paramiko
    finished = True
    stdout = ""
    stderr = ""
    returnCode = None
    buff_size = 1024
    remoteCommand = ""
    if type(command) in [list, tuple]:
        for argument in command:
            remoteCommand += "%s " % pipes.quote(argument)
    else:
        remoteCommand = command

    try:
        client = paramiko.SSHClient()
        # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()
        # mykey = paramiko.RSAKey.from_private_key_file(os.path.expanduser('~/.ssh/id_rsa'))
        # client.connect(host, None, None, mykey)
        client.connect(host)
        chan = client.get_transport().open_session()
        chan.settimeout(timeout_sec)
        chan.exec_command(remoteCommand)
        while not chan.exit_status_ready():
            time.sleep(1)
            if chan.recv_ready():
                stdout += chan.recv(buff_size)

            if chan.recv_stderr_ready():
                stderr += chan.recv_stderr(buff_size)

        returnCode = chan.recv_exit_status()
        while chan.recv_ready():
            stdout += chan.recv(buff_size)
        while chan.recv_stderr_ready():
            stderr += chan.recv_stderr(buff_size)
        client.close()
    except Exception, e:
        logging.exception(e)
        finished = False

    return finished, stdout, stderr, returnCode


def checkCore(nameFormat, searchDirectories, newerThanDateTime, binaryList):
    timeout = 120
    bList = []
    coreFiles = []

    for item in binaryList:
        bList.append("'%s'" % item[:159])

    finished, stdout, stderr, returnCode = runCommandStdOutErrCode(
        ['find'] + searchDirectories + ['-maxdepth', '1', '-name', nameFormat, '-newermt', str(newerThanDateTime),
                                        '-printf', '%p\t', '-exec', 'file', '{}', ';'], timeout)
    if not finished:
        logging.error("Core file search matching %s timed out after %d seconds", nameFormat, timeout)
        return None

    for line in stdout.splitlines():
        sections = line.split('\t', 1)
        for binary in bList:
            if sections[1].endswith(binary):
                coreFiles.append(sections[0])
                break

    return coreFiles


def rmtree(path, retries=3):
    """
    Remove the file or directory
    """

    if not retries or retries < 1:
        return False

    if os.path.isdir(path):
        for i in range(0, retries):
            try:
                shutil.rmtree(path)
                break
            except OSError:
                if i + 1 == retries:
                    return False
                time.sleep(2)
    else:
        for i in range(0, retries):
            try:
                if os.path.exists(path):
                    os.remove(path)
                break
            except OSError:
                if i + 1 == retries:
                    return False
                time.sleep(2)
    return True


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