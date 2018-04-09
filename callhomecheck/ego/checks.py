from common.check import *
from common.util import *
daemons = ['lim', 'vemkd', 'egosc']


class EGOBase(object):
    section = 'EGO'
    pass


class CheckVEMKDResponse(EGOBase, CheckResponse):

    def executeLocalCheck(self):
        finished, output, stderr, returnCode = \
            runCommandStdOutErrCode([getCustomEGOPath(), 'ego', 'info'], self.responseTimeout)
        if not finished:
            return self.returnFail("EGO is unresponsive for %d seconds", self.responseTimeout)
        elif returnCode != 0:
            return self.returnFail("Could not contact EGO")
        return self.returnPass()


class CheckEGOSCResponse(EGOBase, CheckResponse):

    def executeLocalCheck(self):
        finished, output, stderr, returnCode = \
            runCommandStdOutErrCode([getCustomEGOPath(), 'ego', 'info'], self.cmdTimeout)
        if not finished:
            raise CheckErrorException("EGO is unresponsive for %d seconds", self.cmdTimeout)
        elif returnCode != 0:
            raise CheckErrorException("Could not contact EGO")

        finished, output, stderr, returnCode = \
            runCommandStdOutErrCode(
                [getCustomEGOPath(), 'service', 'list', '-s', 'dummy_service'], self.responseTimeout)
        errorText = 'service does not exist'
        if not finished:
            return self.returnFail("Unable to get the list of EGO services. EGO/EGOSC is unresponsive for %d seconds",
                                   self.responseTimeout)
        elif returnCode != 0 and not (errorText in output.lower()):
            return self.returnFail("EGOSC did not respond correctly.")
        return self.returnPass()


class CheckEGODaemon(EGOBase, CheckDaemon):

    def __init__(self, configuration, egoConfig=None):
        # print getRealFile(configuration['BINARY'], egoConfig)
        # print os.path.expandvars('$EGO_WORKDIR')
        binaryPath = getRealFile(configuration['BINARY'], egoConfig)
        super(CheckEGODaemon, self).__init__(configuration, binaryPath)


class CheckEGODir(EGOBase, CheckDir):
    def __init__(self, checkConfig, egoConfig=None):
        dirPath = getRealDir(checkConfig['DIR'], egoConfig)
        super(CheckEGODir, self).__init__(checkConfig, dirPath)


class CheckEGOCore(EGOBase, CheckCore):
    def __init__(self, configuration, egoConfig=None, startCutoffDate=None):
        dirs = configuration.as_list('DIRS')
        for i in range(0, len(dirs)):
            dirs[i] = getRealDir(dirs[i], egoConfig)
        super(CheckEGOCore, self).__init__(
            configuration, getRealFile(configuration['BINARY'], egoConfig), dirs, startCutoffDate)


class CheckEGOServices(EGOBase, CheckModule):

        def executeLocalCheck(self):
            serviceName = self.configuration['NAME']
            finished, output, stderr, returnCode =\
                runCommandStdOutErrCode([getCustomEGOPath(), 'service', 'list', '-s', serviceName], self.cmdTimeout)

            if not finished:
                raise CheckErrorException(
                    "Unable to get the list of EGO services. EGO/EGOSC is unresponsive for %d seconds", self.cmdTimeout)
            lines = output.splitlines()
            if returnCode != 0 or len(lines) < 2 or not lines[0].startswith('SERVICE'):
                raise CheckErrorException("Unable to get information on EGO service %s.", serviceName)
            if lines[1].split()[1] == 'ERROR':
                return self.returnFail("EGO service %s is in the ERROR state", serviceName)
            return self.returnPass()


class CheckEGOCustom(CheckCustom):
    pass
