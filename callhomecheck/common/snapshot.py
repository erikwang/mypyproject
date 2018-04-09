import os
import sys
import imp
import glob
import datetime
from common.log import getLogger

clsnapshotModule = None
snapshotFileFormat = 'CL_Snapshot.*-*-*-*.tar.gz'


def initSnapshotModule(snapshotHome=None):
    global clsnapshotModule
    logger = getLogger(__name__)
    if not clsnapshotModule:
        if not snapshotHome:
            snapshotHome = 'snapshot'
        if not os.path.isabs(snapshotHome):
            snapshotHome = os.path.join(sys.path[0], snapshotHome)
        try:
            sys.path.append(snapshotHome)
            clsnapshotModule = imp.load_source('clsnapshot', os.path.join(snapshotHome, 'clsnapshot.py'))
        except:
            logger.exception("Could not load the Cluster Snapshot module.")
    return bool(clsnapshotModule)


def createClusterSnapshot(snapshotHome='', saveTop='', lsfTop='', egoTop='', loglevel='error', modules=None, **kwargs):
    global clsnapshotModule
    logger = getLogger(__name__)
    initSnapshotModule(snapshotHome)
    generatedSnapFile = None
    if not clsnapshotModule:
        logger.error("Could not load the Cluster Snapshot module.")
        return generatedSnapFile
    origArgv = list(sys.argv)
    error = False

    if not modules:
        modules = ['all']
    else:
        modules = list(modules)

    try:
        if not snapshotHome:
            snapshotHome = os.path.join(sys.path[0], 'clsnapshot')
        if not saveTop:
            saveTop = os.path.join(sys.path[0], 'snapshots')

        params = {'TOP': saveTop, 'LOG_LEVEL': loglevel, 'MODULES': modules}

        for component in ['ego', 'sym', 'lsf']:
            if component in modules or 'all' in modules:
                componentArg = component + '_mdls'
                if componentArg in kwargs:
                    subModules = list(kwargs[componentArg])
                    params[componentArg.upper()] = subModules
                componentLog = component + '_log_level'
                if componentLog in kwargs:
                    params[componentLog.upper()]=kwargs[componentLog]

        generatedSnapFile = clsnapshotModule.runClsSnapshot(params)
    except Exception as e:
        error = True
        logger.exception(e)
    finally:
        sys.argv = origArgv
    if 'queue' in kwargs:
        kwargs['queue'].put(not error, True)
    return generatedSnapFile


def getSnapshotFiles(directory=None):
    if not directory:
        directory = os.path.join(sys.path[0], 'snapshots')
    pattern = os.path.join(directory, snapshotFileFormat)
    return glob.glob(pattern)


def getMinSinceLastSnapshot(directory=None):
    if not directory:
        directory = os.path.join(sys.path[0], 'snapshots')
    pattern = os.path.join(directory, snapshotFileFormat)
    files = glob.glob(pattern)
    files.sort()
    if files and len(files) > 0:
        # 'CL_Snapshot.*-*-*-*.tar.gz'
        dateTime = os.path.basename(files[-1]).split('.')[1].split('-')
        fileDate = datetime.datetime(int(dateTime[0]), int(dateTime[1]), int(dateTime[2]), int(dateTime[3][:2]),
                                     int(dateTime[3][2:4]), int(dateTime[3][4:]))
        td = datetime.datetime.now() - fileDate
    else:
        return sys.maxint
    minutes = -1 * ((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6) / 60
    if minutes < 0:
        minutes = 0
    return minutes


def cleanSnapshots(retentionNum, directory=None):
    logger = getLogger(__name__)
    logger.info("Cleaning up old snapshots...")
    error = False
    if not retentionNum:
        return False
    files = getSnapshotFiles(directory)
    files.sort()
    while len(files) > retentionNum:
        f = files.pop(0)
        try:
            os.remove(f)
            logger.info("Deleted snapshot file %s.", f)
        except EnvironmentError as e:
            logger.exception("Could not delete snapshot file '%s'. Error no %d.", f, e.errno)
            error = True
    return not error
