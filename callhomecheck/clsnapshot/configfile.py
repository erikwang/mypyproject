import os
import sys
sys.path.insert(1, os.path.join('.','modules'))
import configobj
from util import getLogger
import argparse
import clsnapshot
import ego
import lsf
import sym

'''
also habndle command line options:
-s --save-dir=<the directory snapshot data to save, default is /tmp>
-d, --debug info/debug ## turning on debug
-p print logging to stderr while logging
-m, --modules <moulde to run, lsf or sysinfo>
--lsf-modules <lsfRTdata lsfConfig jobHist bk>
--lsf-debug info/debug
--lsf-p print logging to stderr while logging
..
'''


def getClusterSnapshotConfig(configFile=None, arguments=None, preferConfigFile=False):

    logger = getLogger(__name__)
    logLevels = ['critical', 'error', 'warning', 'info', 'debug']
    configFromFile = {}
    if configFile:
        if os.path.isfile(configFile):
                configFromFile = getConfigFromFile(configFile)
        else:
            logger.warn("The snapshot configuration file %s could not be found.", configFile)
    configFromArg = {}
    if arguments:
        parser = argparse.ArgumentParser(description='Spectrum Cluster Snapshot Tool')
        # General arguments.
        parser.add_argument("--source_dir", dest="SOURCE_DIR", metavar="<path>", help="Cluster source file location.")
        parser.add_argument("--save_path", dest="TOP", metavar="<path>", help="Top dir to save snapshot data in.")
        parser.add_argument("--log_level", dest="LOG_LEVEL", default='warning', choices=logLevels,
                            help="debug level")
        parser.add_argument("--log_stderr", dest="verbose", default='n',
                            choices=['y', 'n'], help="Run in verbose mode by printing logging message to stderr.")
        choiceList = getChoiceList(clsnapshot.allMods)
        parser.add_argument("--modules", dest="MODULES", default=['all'], nargs="+", choices=choiceList,
                            help="List of cluster data to collect. Items marked with ~ are explicitly not collected.")
        # LSF arguments.
        choiceList = getChoiceList(lsf.allMods)
        parser.add_argument("--lsf_mdls", dest="LSF_MDLS", default=['all'], nargs="+",
                            choices=choiceList, help="List of LSF data to collect. Items marked with ~ are explicitly "
                                                     "not collected.")
        parser.add_argument("--lsf_log_level", default='warning', dest="LSF_LOG_LEVEL",
                            choices=logLevels, help="Debug level for LSF data collection.")
        parser.add_argument("--lsf_events_num", type=int, dest="EVENTS_NUM",  metavar="<number of lsb.events files>",
                            help="The number of lsb.events* to save")
        # EGO arguments
        choiceList = getChoiceList(ego.allMods)
        parser.add_argument("--ego_mdls", dest="EGO_MDLS", nargs="+", choices=choiceList, default=["all"],
                            help="The comma delimited list of EGO data to collect. Items marked with ~ are never "
                                 "collected.")
        parser.add_argument("--ego_log_level", dest="EGO_LOG_LEVEL", default='warning',
                            choices=logLevels, help="Debug level for EGO data collection.")
        # SYM arguments
        choiceList = getChoiceList(sym.allMods)
        parser.add_argument("--sym_mdls", dest="SYM_MDLS", default=['all'], choices=choiceList, nargs="+",
                            help="The comma delimited list of SYM data to collect. Items marked with ~ are never"
                                 " collected.")
        parser.add_argument("--sym_log_level", default='warning', dest="SYM_LOG_LEVEL",
                            choices=logLevels, help="Debug level for SYM data collection.")
        parser.add_argument("--pkey", action="store", dest="pKey", metavar="<path>",
                            help="Private key file path for logging into remote hosts.")

        configFromArg = vars(parser.parse_args(arguments))

    if preferConfigFile:
        totalConfig = configFromArg
        totalConfig.update(configFromFile)
    else:
        totalConfig = configFromFile
        totalConfig.update(configFromArg)

    return totalConfig


def getConfigFromFile(filePath, ignoreErrors=True):
    try:
        return configobj.ConfigObj(filePath, file_error=True)
    except configobj.ConfigObjError as e:
        if ignoreErrors:
            return e.config
        else:
            raise e


def getChoiceList(allModuleList):
    choiceList = ['all']
    choiceList += list(allModuleList)
    choiceList += ['~' + m for m in allModuleList]
    return choiceList


def getModuleList(parameterList, allModuleList):
    paramSet = set(parameterList)
    allSet = set(allModuleList)
    if 'all'in paramSet:
        enabledMods = set(allSet)
        paramSet.remove('all')
    else:
        enabledMods = allSet.intersection(paramSet)
    for m in paramSet - allSet:
        enabledMods.remove(m[1:])

    return enabledMods
