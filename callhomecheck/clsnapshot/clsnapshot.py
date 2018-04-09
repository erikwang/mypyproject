import tarfile
import errno
from threading import Thread
from datetime import datetime
import imp
import sys
import configfile
import logging
import os
import util

allMods = ['lsf', 'sym', 'ego', 'sysinfo']


def main():
    logger = util.getLogger(__name__)
    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(util.ColorLevelFormatter('%(message)s'))
    out_hdlr.setLevel(logging.INFO)
    logger.addHandler(out_hdlr)

    modulePath = os.path.dirname(os.path.abspath(__file__))
    config = configfile.getClusterSnapshotConfig(os.path.join(modulePath, 'snapshot.conf'), sys.argv[1:])

    logger.info("Starting Cluster Snaphot...")
    sourceDir=config.get('SOURCE_DIR', '')
    sourceFile=''
    if os.path.isfile(os.path.join(sourceDir, "profile.platform")):
        sourceFile = util.sourceEnv(os.path.join(sourceDir, 'profile.platform'))
    elif os.path.isfile(os.path.join(sourceDir, "profile.lsf")):
        sourceFile = util.sourceEnv(os.path.join(sourceDir, 'profile.platform'))

    snapFile = runClsSnapshot(config)
    if snapFile:
        logger.info('Cluster snapshot %s has been created.', snapFile)
    else:
        logger.info('Failed to generate a cluster snapshot.')
        exit(-1)


def runClsSnapshot(config):
    logger = util.getLogger(__name__)

    modulePath = os.path.dirname(os.path.abspath(__file__))
    modname = os.path.splitext(os.path.basename(__file__))[0]
    savePath = config.get('TOP','')
    if not savePath:
        savePath = os.path.join(modulePath, 'snapshots')
        if not os.path.exists(savePath):
            try:
                os.makedirs(savePath)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    logger.error("Could not create save path %s.", savePath)
                    return None
    elif not os.path.exists(savePath):
        logger.error("The save path %s does not exist.", savePath)
        return None

    logFileName = modname + '.log'

    logFile = os.path.join(savePath, logFileName)
    stdErr = config.get('LOG_STDERR', '')
    dbglevel = getattr(logging, config.get('LOG_LEVEL', 'WARN').upper())

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s.%(funcName)s() - %(message)s')
    logfh = logging.FileHandler(logFile, mode='a')
    logfh.setFormatter(formatter)

    logger.addHandler(logfh)
    logger.setLevel(dbglevel)
    if stdErr:
        logstderr = logging.StreamHandler(sys.stderr)
        logstderr.setLevel(dbglevel)
        logstderr.setFormatter(util.LogFileFormatter('%(name)s: %(levelname)s- %(message)s'))
        logger.addHandler(logstderr)

    pKey = config.get('pKey', '')

    if pKey and os.path.isfile(pKey):
        os.putenv('SSH_PRIVATE_KEY', pKey)

    modules = configfile.getModuleList(config.get('MODULES',['all']), allMods)

    mList = list()
    myScriptPath = os.path.dirname(os.path.realpath(__file__))

    for m in modules:
        try:
            mList.append(imp.load_source(__name__ + '.' + m, os.path.join(myScriptPath, m + '.py')))
        except ImportError as e:
            logger.exception("Error loading module as defined in CLI parameter '--modules' or snapshot.conf MODULES"
                             " parameter. Check that the module %s is valid.", m)

    savePath = os.path.abspath(savePath)
    t_list = []
    for mod in mList:
        t_list.append(Thread(target=mod.save, args=[config, savePath]))
        t_list[-1].start()
    for thread in t_list:
        thread.join()
        logger.debug('%s is complete.', thread)

    logger.info('Compressing cluster snapshot...')
    timestr = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    cwd = os.getcwd()
    os.chdir(savePath)
    sstarfile = 'CL_Snapshot.%s.tar.gz' % timestr
    tar = tarfile.open(sstarfile, 'w:gz')
    os.chdir(cwd)
    removeDir = []
    for name in os.listdir(savePath):
        if name.endswith('.tar.gz') or name.endswith('.log'):
            continue
        fullname = os.path.join(savePath, name)
        tar.add(fullname, arcname=name)
        removeDir.append(fullname)
    tar.close()

    for f in removeDir:
        if not util.rmtree(f, 5):
            logger.error("Unable to remove '%s'", f)

    logger.info("Compressed to '%s'", sstarfile)

    return os.path.join(savePath, sstarfile)


if __name__ == "__main__":
    main()
