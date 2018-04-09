from util import *
import socket
from proc import *
import datetime
import time
from distutils.spawn import find_executable
from enum import Enum
from log import getLogger
import glob

class CheckResult(Enum):
    PASS = 0
    PENDING = 1
    WARN = 2
    FAIL = 3


class ExecutionAction(Enum):
    NOTHING = 0
    WARN = 1
    ALERT = 2


class CheckManager(object):

    failedCheckDict = {}

    @staticmethod
    def setFailedChecks(failedChecks):
        CheckManager.failedCheckDict = failedChecks

    @staticmethod
    def getFailedChecks():
        return CheckManager.failedCheckDict

    # def __init__(self, check, description, behaviour="0,n"):
    def __init__(self, checkObj, description):
        # behaviour = check.config['ALERT_THRESHOLD'].split(',')
        self.checkObj = checkObj
        self.checkPath = '|'.join(self.checkObj.getCheckPath())
        self.failLimit = checkObj.configuration['FAIL_LIMIT']
        self.warnLimit = checkObj.configuration['WARN_LIMIT']
        self.failures = []
        self.warnings = []
        self.immediateRetry = checkObj.configuration['RETRY_IMMEDIATELY']
        self.description = description.rstrip('.')
        self.disableOnAlert = True
        if 'DISABLE_ON_ALERT' in checkObj.configuration:
            self.disableOnAlert = checkObj.configuration['DISABLE_ON_ALERT']

    def executeCheck(self, alertCheck=False):
        logger = getLogger(__name__)

        # Skip the check because it is disabled
        if not self.checkObj.configuration['ENABLED']:
            return ExecutionAction.NOTHING
        # Skip the check because it caused an alert before and is in the disable file.
        elif self.checkPath in CheckManager.failedCheckDict:
            if alertCheck:
                return ExecutionAction.NOTHING
            hostName = CheckManager.failedCheckDict[self.checkPath]['HOST']
            errorMessage = CheckManager.failedCheckDict[self.checkPath]['FAIL_MESSAGE'].strip()
            logger.warn("The check %s is currently disabled because it has previously caused an alert on host %s."
                        " Failures:\n%s", self.checkObj.configuration.name, hostName, errorMessage)
            return ExecutionAction.NOTHING
        # The tolerance limit is too small. Assume this check is disabled.
        if self.failLimit < 1:
            return ExecutionAction.NOTHING
        logger.info('Checking %s...', self.description)
        checkPassed = False
        while not checkPassed:
            try:
                checkResult, message = self.checkObj.executeCheck()
                if checkResult == CheckResult.PASS:
                    logger.info('Checking %s passed.', self.description)
                    self.resetFailures()
                    return ExecutionAction.NOTHING
                elif checkResult == CheckResult.PENDING:
                    logger.info('Check result for %s is pending.', self.description)
                elif checkResult == CheckResult.WARN:
                    self.warnings += [message]
                    logger.warning("Check warning %d/%d times.", len(self.warnings), self.warnLimit)
                    if len(self.warnings) >= self.warnLimit:
                        return ExecutionAction.WARN
                elif checkResult == CheckResult.FAIL:
                    if alertCheck:
                        logger.error(message)
                        self.failures = [message]
                        logger.error("Check failed and is considered related to the current alert.")
                    else:
                        logger.error(message)
                        self.failures += [message]
                        logger.error("Check failed %d/%d times.", len(self.failures), self.failLimit)
                    if len(self.failures) >= self.failLimit or alertCheck:
                        return ExecutionAction.ALERT
            except CheckErrorException as e:
                logger.error('Problem encountered running %s check. %s', self.description, str(e))
                return ExecutionAction.NOTHING

            if self.immediateRetry:
                logger.info("Waiting %d seconds before retrying.", self.checkObj.retryWaitTime)
                time.sleep(self.checkObj.retryWaitTime)
            else:
                return ExecutionAction.NOTHING

    def setCheckFailed(self):
        CheckManager.failedCheckDict[self.checkPath] =\
            {'HOST': socket.getfqdn(), 'FAIL_MESSAGE': '\n'.join(self.failures)}

    def resetFailures(self):
        self.failures = []

    def resetWarnings(self):
        self.warnings = []

    def reset(self):
        self.resetFailures()
        self.checkObj.reset()


class CheckErrorException(Exception):
    def __init__(self, *messageArgs):
        numArguments = len(messageArgs)
        message = ""
        if numArguments == 1:
            message = messageArgs[0]
        elif numArguments > 1:
            message = messageArgs[0] % messageArgs[1:]
        super(CheckErrorException, self).__init__(message)


class CheckModule(object):

    def __init__(self, configuration, forceRunLocally=False):
        self.configuration = configuration
        self.responseTimeout = getHierarchicalValue(self.configuration, 'TIMEOUT')
        self.cmdTimeout = getHierarchicalValue(self.configuration, 'CMD_TIMEOUT')
        self.retryWaitTime = configuration['RETRY_WAIT_TIME']
        self.remoteScriptFile = 'remoteclustercheck.py'
        clusterConfig = configuration
        while clusterConfig.depth > 1:
            clusterConfig = clusterConfig.parent
        if clusterConfig['REMOTE_CHECK_HOME'].strip():
            self.remoteScriptFile = os.path.join(clusterConfig['REMOTE_CHECK_HOME'].strip(), self.remoteScriptFile)
        else:
            self.remoteScriptFile = os.path.join(os.getcwd(), self.remoteScriptFile)
        self.pKey = None
        if clusterConfig['SSH_PRIVATE_KEY']:
            self.pKey = clusterConfig['SSH_PRIVATE_KEY']
        self.forceRunLocally = forceRunLocally

    def reset(self):
        return

    def getHost(self):
        return socket.getfqdn()

    def executeCheck(self):
        if self.forceRunLocally:
            host = socket.getfqdn()
        else:
            host = self.getHost()

        if isLocalHost(host):
            return self.executeLocalCheck()
        else:
            return self.executeRemoteCheck(host)

    def executeLocalCheck(self):
        raise NotImplementedError("Abstract class not implemented")

    def executeRemoteCheck(self, host):
        import paramiko
        try:
            finished, output, stdErr, exitCode = runRemoteCommandStdOutErrCode(
                host, ['python', self.remoteScriptFile, '-check', getLongConfigId(self.configuration)],
                self.cmdTimeout, self.pKey)
        except paramiko.AuthenticationException as e:
                raise CheckErrorException("Failed to execute the remote check on host %s. Logon failed: %s", host, e)
        if not finished:
            raise CheckErrorException("Command ssh into %s to check %s process timed out.", host, 'sd')
        for line in output.strip().splitlines():
            if exitCode == 1:
                if line.startswith('FAIL: '):
                    return self.returnFail(line.lstrip('FAIL: '))
                elif line.startswith('WARN: '):
                    return self.returnWarn(line.lstrip('WARN: '))
            if exitCode == 2:
                raise CheckErrorException("The remote check encountered an error while running on host %s.", host)
            elif exitCode != 0:
                raise CheckErrorException("The remote check encountered an error and could not be run on host %s.",
                                          host)
        # return True

    def getCheckPath(self):
        check = self.configuration
        checkPath = [check.name]
        while check.parent.name:
            check = check.parent
            checkPath.append(check.name)
        checkPath.reverse()
        return checkPath

    @staticmethod
    def returnWarn(message, *args):
        # self.warnings.append(message % args)
        return CheckResult.WARN, message % args

    @staticmethod
    def returnFail(message, *args):
        # self.failures.append(error % args)
        return CheckResult.FAIL, message % args

    @staticmethod
    def returnPending(message, *args):
        return CheckResult.PENDING, message % args

    @staticmethod
    def returnPass(*args):
        message = ""
        if len(args) == 1:
            message = args[1]
        elif len(args) > 1:
            message = args[0] % args[1:]
        return CheckResult.PASS, message

    @staticmethod
    def listToString(prefix, theList):
        if len(theList) == 0:
            prefix = ""
        delim = "\n%s" % prefix
        return prefix + delim.join(theList)


class CheckResponse(CheckModule):

    def __init__(self, configuration):
        super(CheckResponse, self).__init__(configuration, False)
        self.timeout = int(configuration['TIMEOUT'])


class CheckDaemon(CheckModule):

    def __init__(self, configuration, daemonPath=None, parameterFilter=None, forceRunLocally=False):
        super(CheckDaemon, self).__init__(configuration, forceRunLocally)
        self.failIfMissing = configuration['FAIL_IF_MISSING']
        self.failIfRestarted = configuration['FAIL_IF_RESTARTED']
        self.minimumUptime = configuration['MINIMUM_UPTIME']

        if daemonPath:
            self.daemonPath = daemonPath
        else:
            self.daemonPath = getRealDir(configuration['BINARY'])
        self.parameterFilter = parameterFilter
        self.daemonName = configuration['NAME']
        # self.memSamples, self.memSampleInterval = parseTwoParamaterInt(configuration['MEM_POLL_CONFIG'])
        namedOptions = namedOptionListToDict(self.configuration['UT_SAMPLING'])
        self.utSamples = namedOptions['SAMPLES']
        self.utSampleInterval = namedOptions['INTERVAL']
        namedOptions = namedOptionListToDict(self.configuration['MEM_SAMPLING'])
        self.memSamples = namedOptions['SAMPLES']
        self.memSampleInterval = namedOptions['INTERVAL']

        # self.memWarn, self.memCrit = parseLimit(configuration['LIMIT_MEM'])
        namedOptions = namedOptionListToDict(self.configuration['MEM_LIMIT'])
        self.memWarn = namedOptions['WARN']
        self.memCrit = namedOptions['ALERT']
        # self.utWarn, self.utCrit = parseLimit(configuration['LIMIT_UT'])
        namedOptions = namedOptionListToDict(self.configuration['MEM_LIMIT'])
        self.utWarn = namedOptions['WARN']
        self.utCrit = namedOptions['ALERT']

        # self.fdWarn, self.fdCrit = parseLimit(configuration['LIMIT_FD'])
        namedOptions = namedOptionListToDict(self.configuration['FD_LIMIT'])
        self.fdWarn = namedOptions['WARN']
        self.fdCrit = namedOptions['ALERT']
        # self.pid = pid
        self.proc = None
        self.hostname = socket.gethostname()

    def reset(self):
        self.proc = None
        super(CheckDaemon, self).reset()

    def updateProcess(self):
        if not (self.proc and self.proc.is_running()):
            if self.proc:
                logging.info("Process %s=%d is no longer running.", self.daemonName, self.proc.pid)
            self.proc = getDaemonProcess(self.daemonPath, self.parameterFilter)
            if not self.proc:
                return False
        return True

    def executeLocalCheck(self):

        logger = getLogger(__name__)

        exitedProcess = None
        if self.proc and not self.proc.is_running():
            exitedProcess = self.proc

        self.updateProcess()

        if not self.proc:
            msg = "Could not find running daemon process with path='%s' on host %s." % (self.daemonPath, self.hostname)
            if self.failIfMissing:
                return self.returnFail(msg)
            else:
                raise CheckErrorException(msg)
        elif self.failIfRestarted and exitedProcess:
            msg = "Process restart detected for %s. Last known pid %d is now %d."\
                  % (self.daemonName, exitedProcess.pid, self.proc.pid)
            return self.returnFail(msg)

        warnMessages = []
        failMessages = []
        exceptionMessage = ""
        try:
            if self.utCrit or self.utWarn:
                # self.proc.cpu_percent(None)
                ut = 0
                for i in range(0, self.utSamples):
                    # time.sleep(self.utSampleInterval)
                    ut = ut + self.proc.cpu_percent(self.utSampleInterval)
                ut = ut / self.utSamples
                if self.utCrit and ut > self.utCrit:
                    failMessages += ['%s (pid=%d) CPU utilization on host %s of %d%% is beyond the critical threshold'
                                     ' of %d%%.' % (self.daemonName, self.proc.pid, self.hostname, ut, self.utCrit)]
                elif self.utWarn and ut > self.utWarn:
                    warnMessages += [
                        "%s (pid=%d) CPU utilization on host %s of %d%% is beyond the warning threshold of %d%%"
                        % (self.daemonName, self.proc.pid, self.hostname, ut, self.utWarn)]

            if self.memCrit or self.memWarn:
                mem = 0
                for i in range(0, self.memSamples):
                    mem += self.proc.memory_info().rss / 1048576
                    time.sleep(self.memSampleInterval)
                mem = mem / self.memSamples
                if self.memCrit and mem > self.memCrit:
                    failMessages += [
                        '%s (pid=%d) memory use on host %s of %dMiB is beyond the critical threshold of %dMiB.'
                        % (self.daemonName, self.proc.pid, self.hostname, mem, self.memCrit)]
                elif self.memWarn and mem > self.memWarn:
                    warnMessages += [
                        '%s (pid=%d) memory use on host %s of %dMiB is beyond the warning threshold of %dMiB.'
                        % (self.daemonName, self.proc.pid, socket.getfqdn(), mem, self.memWarn, )]

            if self.fdCrit or self.fdWarn:
                try:
                    fd = self.proc.num_fds()
                    if self.fdCrit and fd > self.fdCrit:
                        failMessages += [
                            "%s (pid=%d) fd use on host %s of %dMiB is beyond the critical threshold of %dMiB." %
                            (self.daemonName, self.proc.pid, socket.getfqdn(), fd, self.fdCrit)]
                    elif self.fdWarn and fd > self.fdWarn:
                        warnMessages += [
                            '%s (pid=%d) fd use on host %s of %dMiB is beyond the warning threshold of %dMiB.' %
                            (self.daemonName, self.proc.pid, socket.getfqdn(), fd, self.fdWarn)]
                except psutil.AccessDenied:
                    logger.warn('Access denied when trying to read fds for the %s process with pid=%d on host %s.'
                                % (self.daemonName, self.proc.pid, self.hostname))
        except psutil.ZombieProcess:
            exceptionMessage = ("Process (pid=%d, name='%s') is a zombie and has likely exited while being checked on "
                                "host %s." % (self.proc.pid, self.daemonName, self.hostname))
        except psutil.NoSuchProcess:
            exceptionMessage = ("Process (pid=%d, name='%s') no longer exists and has likely exited while being "
                                "checked on host %s." % (self.proc.pid, self.daemonName, self.hostname))

        if len(failMessages):
            return self.returnFail(" ".join(failMessages))
        elif len(warnMessages):
            return self.returnWarn(" ".join(failMessages))
        elif exceptionMessage:
            raise CheckErrorException(exceptionMessage)

        if self.failIfRestarted:
            uptime = int(time.time() - self.proc.create_time())
            if uptime < self.minimumUptime:
                return self.returnPending("Process uptime of %d seconds is less than the minimum of %d seconds."
                                          "Check result is pending.", uptime, self.minimumUptime)
        return self.returnPass()


class CheckDir(CheckModule):
    def __init__(self, configuration, dirPath):
        super(CheckDir, self).__init__(configuration)
        if dirPath:
            self.dirPath = dirPath
        else:
            self.dirPath = getRealDir(configuration['DIR'])
        self.dirName = configuration['NAME']

        # self.useWarn, self.useCrit = parseLimit(self.configuration['SIZE_LIMIT'])
        namedOptions = namedOptionListToDict(self.configuration['SIZE_LIMIT'])
        self.useWarn = namedOptions['WARN']
        self.useCrit = namedOptions['ALERT']
        # self.freeWarn, self.freeCrit = parseLimit(self.configuration['DISK_SPACE_LIMIT'])
        namedOptions = namedOptionListToDict(self.configuration['DISK_SPACE_LIMIT'])
        self.freeWarn = namedOptions['WARN']
        self.freeCrit = namedOptions['ALERT']

    def executeLocalCheck(self):
        if self.dirPath is None or not os.path.isdir(self.dirPath):
            raise CheckErrorException('The path %s does not exist.', self.dirPath)

        total, used, free, percent = psutil.disk_usage(self.dirPath)
        free /= 1000000
        hostname = socket.gethostname()

        used = getDiskUsage(self.dirPath, self.cmdTimeout) / 1000000
        if used < 0:
            raise CheckErrorException('Failed to get the disk usage of %s.', self.dirPath)

        if self.useCrit and used > self.useCrit:
            return self.returnFail('%s directory (%s) disk usage of %dMB is beyond the critical threshold of %dMB on'
                                   ' host %s.' % (self.dirName, self.dirPath, used, self.useCrit, hostname))
        elif self.useWarn and used > self.useWarn:
            return self.returnWarn('%s directory (%s) disk usage of %dMB is beyond the warning threshold of %dMB on'
                                   ' host %s.' % (self.dirName, self.dirPath, used, self.useWarn, hostname))

        if self.freeCrit and free < self.freeCrit:
            return self.returnFail(
                '%s directory (%s) disk space free of %dMB is below the critical threshold of %dMB on'
                ' host %s.' % (self.dirName, self.dirPath, free, self.freeCrit, hostname))
        elif self.freeWarn and free < self.freeWarn:
            return self.returnWarn(
                '%s directory (%s) disk space free of %dMB is below the warning threshold of %dMB on'
                ' host %s.' % (self.dirName, self.dirPath, free, self.freeWarn, hostname))

        return self.returnPass()


class CheckCore(CheckModule):
    def __init__(self, configuration, binPath, searchDirectories=None, startCutoffDate=None, forceRunLocally=False):
        self.binPath = binPath
        self.cutOffDate = startCutoffDate
        if self.cutOffDate is None:
            self.cutOffDate = str(datetime.datetime.now())
        super(CheckCore, self).__init__(configuration, forceRunLocally)

        if os.path.isfile(configuration['BINARY']):
            self.binPath = configuration['BINARY']
        elif os.path.isfile(os.path.expandvars(configuration['BINARY'])):
            self.binPath = os.path.expandvars(configuration['BINARY'])
        elif find_executable(configuration['BINARY']):
            self.binPath = find_executable(configuration['BINARY'])
        else:
            self.binPath = None

        self.coreNameFormat = 'core*.*'
        if configuration['NAME_FORMAT']:
            self.coreNameFormat = configuration['NAME_FORMAT']
        namedOptions = namedOptionListToDict(self.configuration['CORE_LIMIT'])
        self.coreWarn = namedOptions['WARN']
        self.coreCrit = namedOptions['ALERT']
        self.directories = []
        for directory in configuration['DIRS']:
            if os.path.isdir(directory):
                self.directories.append(directory)
            elif os.path.isdir(os.path.expandvars(directory)):
                self.directories.append(os.path.expandvars(directory))

    def reset(self):
        self.cutOffDate = str(datetime.datetime.now())
        super(CheckCore, self).reset()

    def executeLocalCheck(self):
        if not self.binPath:
            # return self.checkResult()
            raise CheckErrorException("Could not find a binary matching %s in the file system",
                                      self.configuration['BINARY'])

        cutOffDate = self.cutOffDate
        self.cutOffDate = str(datetime.datetime.now())
        coreFiles = findCoreFiles(self.coreNameFormat, self.directories, cutOffDate, [self.binPath])
        if coreFiles:
            numCore = len(coreFiles)
            msg = "Core file(s) found on host %s: %s" % (socket.gethostname, ','.join(coreFiles))
            if numCore >= self.coreCrit:
                return self.returnFail(msg)
            elif numCore >= self.coreWarn:
                return self.returnWarn(msg)
        return self.returnPass()


class CheckCustom(CheckModule):

    def __init__(self, configuration):
        super(CheckCustom, self).__init__(configuration)

    def executeLocalCheck(self):
        finished, output, err, exitCode =\
            runCommandStdOutErrCode(self.configuration['COMMAND'], self.responseTimeout, True, True)
        if not finished:
            return self.returnFail("Custom script timed out after %s seconds.", self.responseTimeout)
        elif exitCode not in self.configuration['SUCCESS_EXIT_CODES']:
            return self.returnFail("Script returned with failure exit code %d.", exitCode)
        return self.returnPass()


class CheckBlackHole(CheckModule):

    def __init__(self, configuration):
        super(CheckBlackHole, self).__init__(configuration)

    def executeLocalCheck(self):
        blackHole = self.configuration['DIR']
        nameFormat = self.configuration['NAME_FORMAT']
        fileAction = self.configuration['FILE_ACTION']
        renameSuffix = self.configuration['RENAME_SUFFIX']
        failSuffix = self.configuration['FAIL_SUFFIX']
        moveDir = self.configuration['MOVE_DIR']
        postProcessing = self.configuration['POST_PROCESSING']
        if not os.path.isdir(blackHole):
            raise CheckErrorException("The blackhole directory %s does not exist.", blackHole)

        foundFiles = glob.glob1(blackHole, nameFormat)
        newFiles = []
        if fileAction == 'RENAME':
            for f in foundFiles:
                if not (f.endswith(renameSuffix) or f.endswith(failSuffix)):
                    newFiles.append(f)
        else:
            newFiles = foundFiles

        alerts = {}
        for f in newFiles:
            if postProcessing:
                finished, output, err, exitCode = runCommandStdOutErrCode([postProcessing, os.path.join(blackHole, f)],
                                                                          self.responseTimeout, True, True)
                if finished and exitCode == 0:
                    alerts[f] = output
                else:
                    try:
                        os.rename(os.path.join(blackHole, f), os.path.join(blackHole, f + failSuffix))
                    except IOError:
                        raise CheckErrorException("Post processing failed on alert file %s. Finished: %s Exit code: %d",
                                                  f, finished, exitCode)
            else:
                try:
                    with open(os.path.join(blackHole, f), 'r') as alertFile:
                        alerts[f] = alertFile.read()
                except IOError:
                    raise CheckErrorException("Could not read the contents of alert file %s.", f)

        errorText = []
        if len(alerts):
            errorText.append("Alert files detected.\n")
            for f in alerts:
                if fileAction == 'DELETE':
                    try:
                        os.unlink(os.path.join(blackHole, f))
                    except IOError:
                        raise CheckErrorException("Could not delete alert file %s.", f)
                elif fileAction == 'MOVE':
                    try:
                        os.rename(os.path.join(blackHole, f), os.path.join(moveDir, f))
                    except IOError:
                        raise CheckErrorException("Could not move alert file %s to directory %s.", f, moveDir)
                elif fileAction == 'RENAME':
                    newName = f + renameSuffix
                    try:
                        os.rename(os.path.join(blackHole, f), os.path.join(blackHole, newName))
                    except IOError:
                        raise CheckErrorException("Could not rename alert file %s to %s.", f, newName)

                errorText.append(f)
                errorText.append(':\n')
                errorText.append(alerts[f])
                errorText.append('\n')

            errorText[-1] = errorText[-1].rstrip()
            return self.returnFail(''.join(errorText))

        return self.returnPass()
