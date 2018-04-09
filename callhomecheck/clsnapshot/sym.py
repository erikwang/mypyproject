from time import gmtime, strftime
import sys
import errno
import util
import imp
import os
import logging
import configfile

allMods = ['symRTData', 'symConf', 'symLog']


def save(config, path='/tmp/S_SHUT'):
    modName = os.path.splitext(os.path.basename(__file__))[0]
    savePath = os.path.join(path, modName)
    logFileName = modName + '.log'
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

    thisModPath = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(thisModPath)

    debugLevel = config.get('SYM_LOG_LEVEL')
    LOGFILE = os.path.join(savePath, logFileName)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s.%(funcName)s() - %(message)s')
    fHandle = logging.FileHandler(LOGFILE)
    fHandle.setFormatter(formatter)
    if debugLevel:
        try:
            fHandle.setLevel(getattr(logging, debugLevel.strip().upper()))
        except TypeError:
            pass
    logger.addHandler(fHandle)

    symModules = configfile.getModuleList(config.get('SYM_MDLS', allMods), allMods)
    sym_mods = []
    myScriptPath = os.path.dirname(os.path.realpath(__file__))
    for mod in symModules:
        try:
            sym_mods.append(imp.load_source(__name__ + '.' + mod, os.path.join(myScriptPath, mod + '.py')))
        except ImportError:
            logger.exception("Error loading module as defined in CLI parameter '--sym_mdls' or snapshot.conf SYM_MDLS "
                             "parameter. Check that the module %s is valid.", mod)

    if not os.getenv('SOAM_HOME', ''):
        logger.warn('Cannot find $SOAM_HOME in the environment. Data collection will be incomplete.')

    for mod in sym_mods:
        mod.save(savePath)
    fHandle.close()
    logger.removeHandler(fHandle)
