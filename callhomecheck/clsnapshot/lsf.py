import sys
import logging
from time import gmtime, strftime
import errno
import os
import imp
import configfile
import util

allMods = ['lsfRTdata', 'lsfConf', 'lsfLog', 'jobHist', 'sim', 'sysinfo']

''' parameters supported in [lsf] section in snapshot.conf
    Log_Stderr = Y   #tee logging message to STDERR
    Log_Level = {critical|error|warning|info|debug}
    Collect_Mod = {[lsfRTdata] [lsfConf] [jobHist] [bk]}
'''
Mod_Path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(Mod_Path)


def save(config, path='/tmp/S_SHUT'):
    modName = os.path.splitext(os.path.basename(__file__))[0]
    savePath = os.path.join(path, modName)
    
    logger = util.getLogger(__name__)

    if os.path.exists(savePath):
        dt = strftime("%Y-%m-%d:%H:%M:%S", gmtime())
        os.rename(savePath, savePath + '.' + dt)
    try:
        os.makedirs(savePath)
    except Exception as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            logger.exception("Could not create directory path '%s'.", savePath)
            return

    logFileName = modName + '.log'
    debugLevel = config.get('LSF_LOG_LEVEL')
    LOGFILE = os.path.join(savePath, logFileName)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s.%(funcName)s() - %(message)s')
    fHandle = logging.FileHandler(LOGFILE)
    fHandle.setFormatter(formatter)
    # fHandle.addFilter(util.ReplaceMainFilter())
    if debugLevel:
        try:
            fHandle.setLevel(getattr(logging, debugLevel.strip().upper()))
        except:
            pass
    logger.addHandler(fHandle)

    lsfModules = configfile.getModuleList(config.get('LSF_MDLS', allMods), allMods)
    lsf_mods = []
    myScriptPath = os.path.dirname(os.path.realpath(__file__))

    for mod in lsfModules:
        try:
            lsf_mods.append(imp.load_source(__name__ + '.' + mod, os.path.join(myScriptPath, mod + '.py')))
        except ImportError:
            logger.error("Error loading module as defined in CLI parameter '--lsf_mdls' or snapshot.conf LSF_MDLS "
                         "parameter. Check that the module %s is valid.", mod)

    if not os.getenv('LSF_ENVDIR'):
        logger.warn('Cannot find $LSF_ENVDIR in the environment. Data collection will be incomplete.')

    configFilePath = os.path.join(os.getenv('LSF_ENVDIR', '/etc'), 'lsf.conf')
    lsfConfig = {}
    try:
        lsfConfig = configfile.getConfigFromFile(configFilePath)
    except IOError:
        logger.error("Could not load %s. LSF data collection will be incomplete.", configFilePath)

    for mod in lsf_mods:
        mod.save(config, lsfConfig, savePath)
    fHandle.close()
    logger.removeHandler(fHandle)


def caller_name():
    return os.path.basename(__file__).split('.')[0]
