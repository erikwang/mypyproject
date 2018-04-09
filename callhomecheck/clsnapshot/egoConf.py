import os
from D_Collect import Data_Collect
import util


def save(path='/tmp'):
    logger = util.getLogger(__name__)
    egoConfDir = os.getenv('EGO_CONFDIR')
    if not egoConfDir:
        logger.error('Could not determine the EGO conf directory. Failed to collect EGO log files.')
        return
    elif not os.path.exists(egoConfDir):
        logger.error('The EGO conf directory %s does not exist.', egoConfDir)
    egoConfCp = Data_Collect(path, __name__)
    # for fname in iglob(os.path.join(egoConfDir,'*.conf')):
    #	egoConfCp.copyit(fname)
    # for fname in iglob(os.path.join(egoConfDir,'*.xml')):
    #	egoConfCp.copyit(fname)
    # for fname in iglob(os.path.join(egoConfDir,'*.shared')):
    #	egoConfCp.copyit(fname)
    egoConfCp.copyit(egoConfDir)

    egoServiceConfDir = os.path.join(egoConfDir, '..', '..', 'eservice', 'esc', 'conf', 'services')
    # for fname in iglob(os.path.join(egoServiceConfDir,'*.xml')):
    #	egoConfCp.copyit(fname)
    egoConfCp.copyit(egoServiceConfDir)
