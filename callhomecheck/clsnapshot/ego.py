import os
import logging
from time import gmtime, strftime
import errno
import imp
import configfile
import util

allMods = ['egoRTData', 'egoConf', 'egoWork', 'egoLog']


def save(config, path='/tmp/S_SHUT'):
    modname = os.path.splitext(os.path.basename(__file__))[0]
    savePath = os.path.join(path, modname)
    logFileName = modname + '.log'
    logger = util.getLogger(__name__)
    if os.path.exists(savePath):
        dt = strftime("%Y-%m-%d:%H:%M:%S", gmtime())
        os.rename(savePath, savePath + '.' + dt)
    try:
        os.makedirs(savePath)
    except IOError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            logger.exception("Could not create directory path '%s'.", savePath)
            return

    LOGFILE = os.path.join(savePath, logFileName)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s.%(funcName)s() - %(message)s')
    fHandle = logging.FileHandler(LOGFILE)
    fHandle.setFormatter(formatter)
    # fHandle.addFilter(util.ReplaceMainFilter())
    debugLevel = config.get('EGO_LOG_LEVEL')
    if debugLevel:
        try:
            fHandle.setLevel(getattr(logging, debugLevel.strip().upper()))
        except:
            pass
    logger.addHandler(fHandle)
    egoModules = configfile.getModuleList(config.get('EGO_MDLS', allMods), allMods)
    ego_mods = []
    myScriptPath = os.path.dirname(os.path.realpath(__file__))
    for mod in egoModules:
        try:
            ego_mods.append(imp.load_source(__name__ + '.' + mod, os.path.join(myScriptPath, mod + '.py')))
        except ImportError:
            logger.exception("Error loading module as defined in CLI parameter '--ego_mdls' or snapshot.conf EGO_MDLS "
                             "parameter. Check that the module %s is valid.", mod)
    if not os.getenv('EGO_TOP', ''):
        logger.warn('Cannot find $EGO_TOP in the environment. EGO data collection will be incomplete.')
    for mod in ego_mods:
        mod.save(savePath)
    fHandle.close()
    logger.removeHandler(fHandle)
