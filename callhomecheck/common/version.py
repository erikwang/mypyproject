import sys
from log import getLogger
from distutils.version import LooseVersion

def checkPythonVersion():
    logger = getLogger(__name__)
    if sys.version_info < (2, 6, 6) or sys.version_info[0] >= 3:
        logger.critical(
            "This version of Python is not supported. Only Python 2.x versions 2.6.6 and newer are supported."
            "Exiting...")
        exit(-1)


def checkPsutilVersion():
    logger = getLogger(__name__)
    try:
        import psutil
        if LooseVersion(psutil.__version__) < LooseVersion('4.1.0'):
            logger.critical(
                "The installed version of psutil (%s) is not supported."
                "Only versions 4.1.0 and later are supported. Exiting...", psutil.__version__)
            exit(-1)
    except ImportError:
        logger.critical("Could not load the psutil module. Exiting...")
        exit(-1)


def checkParamikoVersion():
    logger = getLogger(__name__)
    try:
        import paramiko
        if LooseVersion(paramiko.__version__) < LooseVersion('2.0.0'):
            logger.critical("The installed version of paramiko (%s) is not supported."
                            " Only versions 2.0.0 and later are supported. Exiting...", paramiko.__version__)
            exit(-1)
    except ImportError:
        logger.critical("Could not load the paramiko module. Paramiko is required when ECC_HOST is set to run on a"
                        " separate host or when Symphony checking is enabled. Exiting.")
        exit(-1)