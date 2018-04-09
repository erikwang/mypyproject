import os
import subprocess
import signal
from threading import Timer
import logging
import sys
import socket
import pipes
import time
from log import getLogger
import getpass
import glob
from distutils.spawn import find_executable
import configobj
import platform

egoshCommand = None


def getRealPath(path, config=None, isFile=False):
    if not path:
        return None
    elif isFile:
        testFunction = os.path.isfile
    else:
        testFunction = os.path.isdir

    if testFunction(path):
        return path

    tmp = os.path.expandvars(path)
    if testFunction(tmp):
        return tmp

    pathParts = path.split(os.sep)
    if config and pathParts[0] in config and config[pathParts[0]].strip():
        newPath = str(path).replace(pathParts[0], config[pathParts[0]].strip(), 1)
        if testFunction(newPath):
            return newPath

    if isFile:
        return find_executable(path)

    return None


def getRealFile(directory, config=None):
    return getRealPath(directory, config, True)


def getRealDir(directory, config=None):
    return getRealPath(directory, config)


def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def getFullCheckPath(checkSection):
    path = []
    while checkSection.parent is not checkSection:
        path.insert(0, checkSection.name)
    return path


def getLongConfigId(config):
    path = ''
    while config.parent is not config:
        path = "%s#%s" % (config.name, path)
        config = config.parent
    return path.strip('#')


def sourceEnv(sourceFile):
    command = ['bash', '-c', 'source ' + sourceFile + ' && set']
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in proc.stdout:
        (key, _, value) = line.rstrip('\r\n').partition("=")
        os.environ[key] = value
    proc.communicate()


def runCommand(command, timeout_sec, useShell=False):
    finished, stdout, stderr, exitCode = runCommandStdOutErrCode(command, timeout_sec, useShell=useShell)
    if not finished:
        return None
    return stdout


def runCommandCode(command, timeout_sec, useShell=False):
    finished, stdout, stderr, exitCode = runCommandStdOutErrCode(command, timeout_sec, useShell=useShell)
    if not finished:
        stdout = None
    return stdout, exitCode


def runCommandStdOutErrCode(command, timeout_sec, useShell=False, splitStdErr=False):
    finished = True

    stderrDestination = subprocess.STDOUT
    if splitStdErr:
        stderrDestination = subprocess.PIPE
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=stderrDestination, shell=useShell)

    def kill_proc(p): p.kill()

    timer = Timer(timeout_sec, kill_proc, [proc])
    try:
        timer.start()
        stdout, stderr = proc.communicate()
    finally:
        timer.cancel()

    if proc.returncode == -signal.SIGKILL:
        finished = False
    return finished, stdout, stderr, proc.returncode


def runRemoteCommandStdOutErrCode(host, command, timeout_sec, pKeyFile=None):
    import paramiko
    finished = True
    stdout = ""
    stderr = ""
    buff_size = 1024
    remoteCommand = ""
    if type(command) in (list, tuple):
        for argument in command:
            remoteCommand = "%s %s" % (remoteCommand, pipes.quote(argument.encode('string_escape')))
    else:
        remoteCommand = command

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cfg = {'hostname': socket.getfqdn(host), 'username': getpass.getuser()}

    if pKeyFile:
        cfg['pkey'] = paramiko.RSAKey.from_private_key_file(pKeyFile)
    else:
        ssh_config = paramiko.SSHConfig()
        user_config_file = os.path.expanduser("~/.ssh/config")
        if os.path.exists(user_config_file):
            with open(user_config_file) as f:
                ssh_config.parse(f)
        user_config = ssh_config.lookup(cfg['hostname'])
        for k in ('hostname', 'username', 'port'):
            if k in user_config:
                cfg[k] = user_config[k]
        if 'identityfile' in user_config:
            cfg['key_filename'] = user_config['identityfile']
        if 'proxycommand' in user_config:
            cfg['sock'] = paramiko.ProxyCommand(user_config['proxycommand'])

    client.connect(**cfg)
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

    return finished, stdout, stderr, returnCode


def printError(level, error):
    levelText = ''
    if level == 1:
        levelText = 'FAIL'
    elif level == 2:
        levelText = 'WARN'
    return '%s: %s' % (levelText, error)


def parseLimit(limitList, appName=None):
    return parseTwoParamaterInt(parseCheckOption(limitList, appName))


def parseCheckOption(optionList, appName):
    if appName:
        appName += ':'
    value = ''
    for option in optionList.split():
        if appName and option.startswith(appName):
            value = option[len(appName):]
            break
        elif ':' not in option:
            value = option
    return value


def parseTwoParamaterInt(listStr):
    temp = listStr.split(',')
    p1 = None
    p2 = None
    length = len(temp)
    if length >= 2 and temp[1].isdigit():
        p2 = int(temp[1])
    if length >= 1 and temp[0].isdigit():
        p1 = int(temp[0])

    return p1, p2


def getDiskUsage(path, timeout=None):

    logger = getLogger(__name__)

    if platform.system() == 'Linux':

        output, exitCode = runCommandCode(['du', '-s', path], timeout)
        if output.strip() is None:
            logger.error("The du command timed out after %d seconds.", path, timeout)
            return -1

        byteString = output.splitlines()[-1].split()
        if byteString:
            try:
                kilobytes = int(byteString[0])
                if exitCode:
                    logger.warn("The du command exited with code %d when checking disk usage of %s. "
                                "The reported disk usage of %dK is likely less than actual.", exitCode, path, kilobytes)
                return kilobytes * 1024
            except ValueError:
                pass
        logger.error("The du command could not get the disk usage of %s.")

        return -1

    total = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                logger.warn("Could not get the file size %s.", os.path.join(root, name))
    return total


def getMandatoryEnvVar(varName):
        logger = getLogger(__name__)
        value = os.getenv(varName)
        if value is None:
            msg = 'Cannot find %s in the sourced environment. Exiting...' % varName
            logger.critical(msg)
            exit(-1)
        return value


def getClusterInfo(componentList, timeout=None):
    clusterName = None
    masterName = None
    egoEnabled = 'EGO' in componentList
    if egoEnabled:
        finished, stdout, stderr, returnCode = runCommandStdOutErrCode(['egosh', 'ego', 'info'], timeout)
    else:
        finished, stdout, stderr, returnCode = runCommandStdOutErrCode(['lsid'], timeout)
    if finished and returnCode == 0:
        for line in stdout.splitlines():
            if egoEnabled:
                if line.startswith('Cluster name'):
                    clusterName = line.split(':', 1)[1].strip()
                elif line.startswith('EGO master host name'):
                    masterName = socket.getfqdn(line.split(':', 1)[1].strip())
            else:
                if line.startswith('My cluster name is'):
                    clusterName = line.replace('My cluster name is', '', 1).strip()
                elif line.startswith('My master name is'):
                    masterName = socket.getfqdn(line.replace('My master name is', '', 1).strip())

    return clusterName, masterName


def getCustomEGOPath():
    global egoshCommand
    if not egoshCommand:
        if os.path.isfile(os.path.join(sys.path[0], 'egosh')):
            egoshCommand = os.path.join(sys.path[0], 'egosh')
        else:
            egoshCommand = 'egosh'
    return egoshCommand


def findCoreFiles(nameFormat, searchDirectories, newerThanEpoch, binaryList):
    timeout = 120
    logger = getLogger(__name__)

    returnFiles = []
    for directory in searchDirectories:
        filesFound = glob.glob1(directory, nameFormat)
        filesFound = [x for x in filesFound if os.path.getmtime(x) >= newerThanEpoch]
        if len(filesFound) == 0:
            return returnFiles
        finished, stdout, stderr, returnCode = \
            runCommandStdOutErrCode(['file'] + filesFound, timeout)
        if finished and not returnCode:
            fileResults = stdout.splitlines()
            if len(fileResults) == len(filesFound):
                for i in range(0, len(fileResults)):
                    if fileResults[i].startswith(filesFound[i] + ':'):
                        parts = fileResults[i].replace(filesFound[i] + ':', '', 1).split(' from ', 1)
                        if len(parts) == 2 and ' core file ' in parts[0] and \
                                any(item.startswith(parts[1][1:-1]) for item in binaryList):
                            returnFiles.append(filesFound[i])
                    else:
                        logger.error("The 'file' command did not return the expected output.")
            else:
                logger.error("The 'file' command did not return the expected number of lines.")
        elif finished:
            logger.error("There was an error running the 'file' command.")
        else:
            logger.error("Running the 'file' command timed out.")

    return returnFiles


class NullHandler(logging.Handler):
        def emit(self, record):
            pass


def createPMRCreateCommand(component, version, summary, body, email, clusterName=None, configFile=None):

    if not email:
        email = 'your_email@server.com'

    command = ['python', 'callhomepmr.py']
    if configFile:
        command.append('--config')
        command.append("'%s'" % configFile)
    command.append('create')
    command.append('-e')
    command.append("'%s'" % email)
    command.append('-co')
    command.append("'%s'" % component)
    if clusterName:
        command.append('-cn')
        command.append("'%s'" % clusterName)
    command.append('-ve')
    command.append("'%s'" % version)
    command.append("'%s'" % summary)
    command.append("'%s'" % body.replace('\n', '\\n'))

    return " ".join(command)


def createPMRUploadCommand(uri, configFile=None, files=None):
    command = ['python', 'callhomepmr.py']
    if configFile:
        command.append('--config')
        command.append("'%s'" % configFile)
    command.append('upload')
    command.append("'%s'" % uri)
    if files:
        for f in files:
            command.append("'%s'" % f)

    return " ".join(command)


def isLocalHost(hostName):
    return socket.getfqdn(hostName) in (socket.getfqdn(), socket.getfqdn('localhost'))


def getHierarchicalValue(config, attribute):
    if attribute in config and config[attribute]:
        return config[attribute]
    elif config.parent and config.parent != config:
        return getHierarchicalValue(config.parent, attribute)
    return None


def namedOptionListToDict(namedOptionList):
    logger = getLogger(__name__)
    returnDict = {}
    if isinstance(namedOptionList, str):
        itemList = namedOptionList.split(',')
    else:
        itemList = namedOptionList
    for item in itemList:
        temp = item.split(':')
        if len(temp) != 2 or len(temp[0].strip()) == 0 or len(temp[1].strip()) == 0:
            logger.error("Could not parse list %s to dictionary.", namedOptionList)
            return None
        try:
            val = int(temp[1])
        except ValueError:
            logger.error("Could not parse list %s to dictionary.", namedOptionList)
            return None
        returnDict[temp[0].strip()] = val
    return returnDict


def updateDisableFile(disableFile, disabledCheckDict):
    tempFile = disableFile + ".tmp"
    logger = getLogger(__name__)
    newDisabledConfig = configobj.ConfigObj()
    newDisabledConfig.merge(disabledCheckDict)
    try:
        with open(tempFile, "w+") as f:
            newDisabledConfig.write(f)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tempFile, disableFile)
    except IOError:
        logger.exception("Could not update the disable file '%s'.", disableFile)
        return False
    return True


def readDisableFile(disableFile):
    logger = getLogger(__name__)
    disabledCheckDictionary = {}
    import configobj
    if os.path.isfile(disableFile):
        try:
            disabledCheckDictionary = configobj.ConfigObj(disableFile)
        except configobj.ConfigObjError as e:
            disabledCheckDictionary = e.config
        except IOError:
            logger.exception("Could not read '%s'.", disableFile)
            return None
    return disabledCheckDictionary