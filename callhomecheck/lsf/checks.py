from common.check import *
from common.util import *
import time

daemons = ['lim', 'mbatchd', 'mbschd', 'sbatchd']


class LSFBase(object):
    section = 'LSF'
    pass


class CheckMLIMResponse(LSFBase, CheckResponse):

    def executeLocalCheck(self):
        try:
            output, exitCode = runCommandCode(['lsid'], self.timeout)
        except OSError as e:
            raise CheckErrorException(e)
        if output is None:
            return self.returnFail("LIM is unresponsive for %d seconds.", self.timeout)
        elif exitCode != 0:
            return self.returnFail("Error running lsid. Could not contact the cluster.")
        return self.returnPass()


class CheckMBDResponse(LSFBase, CheckResponse):

    def __init__(self, configuration):
        super(CheckMBDResponse, self).__init__(configuration)

    def executeLocalCheck(self):

        try:
            output, exitCode = runCommandCode(self.configuration['COMMAND'].split(), self.timeout)
        except OSError as e:
            raise CheckErrorException(e)

        if output is None:
            return self.returnFail("MBD is unresponsive for %d seconds.", self.timeout)

        return self.returnPass()


class CheckLSFDaemon(LSFBase, CheckDaemon):
    def __init__(self, configuration, lsfConfig):
        binaryPath = getRealFile(configuration['BINARY'], lsfConfig)
        super(CheckLSFDaemon, self).__init__(configuration, binaryPath or configuration['BINARY'])


class CheckBLDaemon(LSFBase, CheckDaemon):

    def getHost(self):
        finished, output, err, exitCode = \
            runCommandStdOutErrCode(['blhosts'], self.cmdTimeout)
        if not finished:
            raise CheckErrorException(
                "Failed to get bld host. Bld is unresponsive for %d seconds", self.cmdTimeout)
        if exitCode != 0:
            raise CheckErrorException("Failed to get the bld host.")
        lines = output.splitlines()
        for line in lines:
            if line.startswith("master:"):
                if line.split(':', 1)[-1].strip():
                    return []
                else:
                    return [line.split(':', 1)[-1].strip()]
        raise CheckErrorException("Could not determine the bld host.")


class CheckBLDDaemon(CheckBLDaemon):
    def __init__(self, configuration, lsfConfig, forceRunLocally=False):
        binaryPath = getRealFile(configuration['BINARY'], lsfConfig)
        super(CheckBLDDaemon, self).__init__(configuration, binaryPath or configuration['BINARY'],
                                             None, forceRunLocally)


class CheckBlcollectDaemon(CheckBLDaemon):

    def __init__(self, configuration, forceRunLocally=False):
        binaryPath = getRealFile(configuration['BINARY'])
        self.collectorName = configuration['COLLECTOR_NAME'].strip()
        super(CheckBlcollectDaemon, self).__init__(
            configuration, binaryPath or configuration['BINARY'], '-a %s' % self.collectorName, forceRunLocally)


class CheckLSFDir(LSFBase, CheckDir):
    def __init__(self, checkConfig, lsfConfig=None):
        serverDir = getRealDir(checkConfig['DIR'], lsfConfig)
        super(CheckLSFDir, self).__init__(checkConfig, serverDir)


class CheckLSFCore(LSFBase, CheckCore):
    def __init__(self, configuration, lsfConfig=None, startCutoffDate=None):
        dirs = configuration.as_list('DIRS')
        for i in range(0, len(dirs)):
            dirs[i] = getRealDir(dirs[i], lsfConfig)
        super(CheckLSFCore, self).__init__(configuration, getRealFile(configuration['BINARY']), dirs, startCutoffDate)


class CheckSchedInterval(LSFBase, CheckModule):

    def __init__(self, configuration):
        super(CheckSchedInterval, self).__init__(configuration)
        namedOptions = namedOptionListToDict(self.configuration['INTERVAL_SAMPLING'])
        self.sampleInterval = namedOptions['INTERVAL']
        self.samples = int(namedOptions['SAMPLES'])
        namedOptions = namedOptionListToDict(self.configuration['INTERVAL_LIMIT'])
        self.warn = namedOptions['WARN']
        self.fail = namedOptions['ALERT']

    def executeLocalCheck(self):
        warnCount = -1
        failCount = -1
        for i in range(0, self.samples):
            try:
                output, exitCode = runCommandCode(['badmin', 'perfmon', 'view'], self.cmdTimeout)
            except OSError as e:
                raise CheckErrorException(e)
            if output is None:
                raise CheckErrorException("MBD was unresponsive for %d seconds.", self.cmdTimeout)
            elif exitCode == 7:
                logging.warn("The performance monitor is not enabled.")
                return self.returnPass()
            for line in output.splitlines():
                if line.startswith('Scheduling interval in second(s)'):
                    values = line.replace('Scheduling interval in second(s)', '', 1).split()
                    lastSchedulingInterval = int(values[0])
                    if lastSchedulingInterval > self.warn:
                        warnCount += 1
                    if lastSchedulingInterval > self.fail:
                        failCount += 1
                    if warnCount < i and failCount < i:
                        return self.returnPass()
                    break
                elif line.startswith('No performance metric data available'):
                    raise CheckErrorException("The performance monitor does not have results yet.")
            time.sleep(self.sampleInterval)
        if failCount == self.samples:
            return self.returnFail("The last %s scheduling intervals were over the fail limit of %s.",
                                   self.samples, self.fail)
        elif warnCount == self.samples:
            return self.returnWarn("The last %s scheduling intervals were over the warn limit of %s.",
                                   self.samples, self.fail)
        return self.returnPass()


class CheckLSFBlackhole(CheckBlackHole):
    pass


class CheckLSFCustom(CheckCustom):
    pass


class CheckBLDResponse(LSFBase, CheckModule):

    def __init__(self, configuration):
        super(CheckBLDResponse, self).__init__(configuration)

    def executeLocalCheck(self):
        try:
            output, exitCode = runCommandCode(['blstat'], self.responseTimeout)
        except OSError as e:
            raise CheckErrorException(e)
        if output is None:
            return self.returnFail("Bld is unresponsive for %d seconds.", self.responseTimeout)
        elif exitCode != 0:
            return self.returnFail("Error running blstat. There was an error contacting bld.")
        return self.returnPass()


class CheckBlcollectResponse(LSFBase, CheckModule):

    def __init__(self, configuration):
        super(CheckBlcollectResponse, self).__init__(configuration)

    def executeLocalCheck(self):
        collectorName = self.configuration['COLLECTOR_NAME']
        try:
            output, exitCode = runCommandCode(['blcstat', collectorName], self.cmdTimeout)
        except OSError as e:
            raise CheckErrorException(e)
        print output
        if output is None:
            raise CheckErrorException("Bld is unresponsive for %d seconds.", self.cmdTimeout)
        if exitCode != 0:
            raise CheckErrorException("Error encountered running blcstat.")
        output = output.strip()
        if not output:
            raise CheckErrorException("Did not get any information for collector %s from blcstat.", collectorName)
        lines = output.splitlines()
        if len(lines) != 2:
            raise CheckErrorException("Unexpected output from blcstat.")
        values = lines[-1].split()
        if len(values) < 3:
            raise CheckErrorException("Unexpected collector data from blcstat.")
        if values[1] != 'ok':
            return self.returnFail("The collector %s is currently %s.", collectorName, values[1])
        return self.returnPass()
