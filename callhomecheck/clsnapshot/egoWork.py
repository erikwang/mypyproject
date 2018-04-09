import os
from D_Collect import Data_Collect
import util


def save(path='/tmp'):
    logger = util.getLogger(__name__)
    egoConfDir = os.getenv("EGO_CONFDIR")
    if not egoConfDir:
        logger.error('Could not determine the EGO conf directory. Failed to collect EGO work directory files.')
        return

    egoWorkDir = os.path.join(egoConfDir, '..', 'work')
    if not os.path.exists(egoWorkDir):
        logger.error('The EGO work directory %s does not exist. Failed to collect EGO work directory files.',
                     egoWorkDir)
        return
    egoConfCp = Data_Collect(path, __name__)
    egoConfCp.copyit(egoWorkDir)
