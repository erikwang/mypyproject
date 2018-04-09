from common.check import *
from common.util import *
import socket

daemons = ['sd', 'ssm']


class SYMBase(object):
    section = 'SYM'
    remoteScriptFile = 'remoteclustercheck.py'
    pass


class CheckSDResponse(SYMBase, CheckResponse):

    def executeLocalCheck(self):

        finished, output, stderr, returnCode = \
            runCommandStdOutErrCode(['soamview', 'app'], self.responseTimeout)
        if not finished:
            return self.returnFail("SD is unresponsive for %d seconds.", self.responseTimeout)
        elif output.startswith('No applications found'):
            return self.returnPass()
        elif returnCode == 85 or returnCode == 214:
            return self.returnFail("Error running 'soamview app'. SD is not up.")
        elif returnCode != 0 or not output.startswith('APPLICATION'):
            return self.returnFail("Error running 'soamview app'. Cannot contact SD.")

        return self.returnPass()


class CheckSSMResponse(SYMBase, CheckResponse):

    def executeLocalCheck(self):

        appName = self.configuration['APPLICATION']
        finished, output, stdErr, exitCode = runCommandStdOutErrCode(['soamview', 'app', appName], self.cmdTimeout)
        if not finished:
            raise CheckErrorException("SD is unresponsive for %d seconds.", self.cmdTimeout)
        elif exitCode == 85 or exitCode == 214:
            raise CheckErrorException("SD is not up.")
        elif exitCode == 81:
            raise CheckErrorException("Application %s does not exist.", appName)
        elif exitCode != 0 or not output.startswith('APPLICATION'):
            raise CheckErrorException("Error running 'soamview app'. Cannot contact SD.")

        status = output.splitlines()[1].split()[1]
        if status != 'enabled':
            return self.returnPass()

        finished, output, stdErr, exitCode = \
            runCommandStdOutErrCode(['soamview', 'app', appName, '-l'], self.responseTimeout)
        if not finished:
            return self.returnFail("SSM is unresponsive after %d seconds." % self.responseTimeout)
        return self.returnPass()


class CheckSDDaemon(SYMBase, CheckDaemon):

    def __init__(self, configuration, forceLocalCheck=False):
        binaryPath = getRealFile(configuration['BINARY'])
        super(CheckSDDaemon, self).__init__(configuration, binaryPath or configuration['BINARY'], None, forceLocalCheck)
        self.timeout = configuration['TIMEOUT']

    def getHost(self):
        finished, output, err, exitCode = \
            runCommandStdOutErrCode([getCustomEGOPath(), 'service', 'list', '-s', 'SD'], self.cmdTimeout)
        if not finished:
            raise CheckErrorException(
                "Unable to get the list of EGO services. EGO/EGOSC is unresponsive for %d seconds", self.cmdTimeout)
        lines = output.splitlines()
        if exitCode != 0 or len(lines) != 2 or not lines[0].startswith('SERVICE'):
            raise CheckErrorException("Unable to get information on EGO service SD.")
        serviceLine = lines[1].split()
        if serviceLine[1] != 'STARTED' or serviceLine[-2] != 'RUN':
            return []
        if not serviceLine[-1].isdigit() or int(serviceLine[-1]) <= 0:
            raise CheckErrorException("The egosh command returned unexpected output. Cannot get SD's activity ID.")

        activityID = serviceLine[-1]
        finished, output, err, exitCode = \
            runCommandStdOutErrCode([getCustomEGOPath(), 'activity', 'view', serviceLine[-1]], self.cmdTimeout)
        if not finished:
            raise CheckErrorException(
                "Unable to get SD's activity information. EGO/EGOSC is unresponsive for %d seconds", self.cmdTimeout)
        lines = output.splitlines()
        if len(lines) < 8:
            raise CheckErrorException("Unable to get activity information for ID %s from EGO.", activityID)
        activityHost = ''
        for line in lines:
            lineParts = line.split(':', 1)
            if lineParts[0].startswith('Resource Name') \
                    and lineParts[0].strip() == 'Resource Name' and len(lineParts) == 2:
                activityHost = lineParts[-1]
                break

        activityHost = activityHost.strip()
        if not activityHost.strip():
            raise CheckErrorException("Unable to determine the SD host using allocation ID %s.", activityID)
        return activityHost


class CheckSSMDaemon(SYMBase, CheckDaemon):

    def __init__(self, configuration, remoteCheck=False):
        binaryPath = getRealFile(configuration['BINARY'])
        self.appName = configuration['APPLICATION'].strip()
        super(CheckSSMDaemon, self).__init__(configuration, binaryPath or configuration['BINARY'],
                                             '-a %s' % self.appName, remoteCheck)
        self.timeout = configuration['TIMEOUT']
        self.ssmPID = -1
        # self.daemonPath=configuration['BINARY']
        self.hostname = socket.getfqdn()

    def getHost(self):
        appName = self.configuration['APPLICATION']
        finished, output, err, exitCode = \
            runCommandStdOutErrCode(['soamview', 'app', appName, '-l'], self.cmdTimeout)
        if not finished:
            raise CheckErrorException(
                "Failed to get application information for %s. EGO/EGOSC is unresponsive for %d seconds",
                appName, self.cmdTimeout)
        if exitCode != 0 or not output.startswith('Application name:'):
            raise CheckErrorException("Unable to get application information for %s.", appName)
        lines = output.splitlines()
        for line in lines:
            if line.startswith("Status:"):
                if line.split(':', 1)[-1].strip() != 'enabled':
                    return ""
            elif line.startswith("SSM host:"):
                hostName = line.split(':', 1)[-1].strip()
                if hostName != '-':
                    return hostName
                else:
                    return None
        raise CheckErrorException("Could not determine the SSM host for application %s.", appName)


class CheckSYMDir(SYMBase, CheckDir):
    def __init__(self, configuration, symConfig=None, startCutoffDate=None):
        dirs = getRealDir(configuration['DIR'], symConfig)
        super(CheckSYMDir, self).__init__(configuration, dirs)


class CheckSYMCore(SYMBase, CheckCore):
    def __init__(self, configuration, symConfig=None, startCutoffDate=None, forceRunLocally=False):
        dirs = configuration.as_list('DIRS')
        for i in range(0, len(dirs)):
            dirs[i] = getRealDir(dirs[i], symConfig)
        super(CheckSYMCore, self).__init__(configuration, getRealFile(configuration['BINARY'], symConfig)
                                           or configuration['BINARY'], dirs, startCutoffDate, forceRunLocally)


class CheckSSMCore(CheckSYMCore):

    def getHost(self):
        appName = self.configuration['APPLICATION']
        finished, output, err, exitCode = \
            runCommandStdOutErrCode(['soamview', 'app', appName, '-l'], self.cmdTimeout)
        if not finished:
            raise CheckErrorException(
                "Failed to get application information for %s. EGO/EGOSC is unresponsive for %d seconds",
                appName, self.cmdTimeout)
        if exitCode != 0 or not output.startswith('Application name:'):
            raise CheckErrorException("Unable to get application information for %s.", appName)
        lines = output.splitlines()
        for line in lines:
            if line.startswith("Status:"):
                if line.split(':', 1)[-1].strip() != 'enabled':
                    return ""
            elif line.startswith("SSM host:"):
                hostName = line.split(':', 1)[-1].strip()
                if hostName != '-':
                    return hostName
                else:
                    return None

        raise CheckErrorException("Could not determine the SSM host for application %s.", appName)


class CheckSDCore(CheckSYMCore):

    def getHost(self):
        finished, output, err, exitCode = \
            runCommandStdOutErrCode([getCustomEGOPath(), 'service', 'list', '-s', 'SD'], self.cmdTimeout)
        if not finished:
            raise CheckErrorException(
                "Unable to get the list of EGO services. EGO/EGOSC is unresponsive for %d seconds", self.cmdTimeout)
        lines = output.splitlines()
        if exitCode != 0 or len(lines) != 2 or not lines[0].startswith('SERVICE'):
            raise CheckErrorException("Unable to get information on EGO service SD.")
        serviceLine = lines[1].split()
        if serviceLine[1] != 'STARTED' or serviceLine[-2] != 'RUN':
            return ""
        if not serviceLine[-1].isdigit() or int(serviceLine[-1]) <= 0:
            raise CheckErrorException("The egosh command returned unexpected output. Cannot get SD's activity ID.")

        activityID = serviceLine[-1]
        finished, output, err, exitCode = \
            runCommandStdOutErrCode([getCustomEGOPath(), 'activity', 'view', serviceLine[-1]], self.cmdTimeout)
        if not finished:
            raise CheckErrorException(
                "Unable to get SD's activity information. EGO/EGOSC is unresponsive for %d seconds", self.cmdTimeout)
        lines = output.splitlines()
        if len(lines) < 8:
            raise CheckErrorException("Unable to get activity information for ID %s from EGO.", activityID)
        activityHost = ''
        for line in lines:
            lineParts = line.split(':', 1)
            if lineParts[0].startswith('Resource Name') \
                    and lineParts[0].strip() == 'Resource Name' and len(lineParts) == 2:
                activityHost = lineParts[-1]
                break

        activityHost = activityHost.strip()
        if not activityHost.strip():
            raise CheckErrorException("Unable to determine the SD host using allocation ID %s.", activityID)
        return activityHost


class CheckSYMCustom(CheckCustom):
    pass
