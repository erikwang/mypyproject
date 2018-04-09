import os
from D_Collect import Data_Collect
import util


def save(path='/tmp'):
    logger = util.getLogger(__name__)
    symConfCp = Data_Collect(path, __name__)
    egoConfDir = os.getenv('EGO_CONFDIR')
    if not egoConfDir:
        logger.error("Could not determine the EGO conf directory. Failed to collect Symphony configuration files.")
        return
    profileDir = os.path.join(egoConfDir, '..', '..', 'soam', 'profiles')
    egoServiceConfDir = os.path.join(egoConfDir, '..', '..', 'eservice', 'esc', 'conf', 'services')
    if os.path.exists(profileDir):
        symConfCp.copyit(profileDir)
    else:
        logger.error("The Symphony application profile directory %s does not exist. "
                     "Failed to copy application profiles.", profileDir)
    if os.path.exists(egoServiceConfDir):
        symConfCp.copyit(egoServiceConfDir)
    else:
        logger.error("The EGO service profile directory %s does not exist. Failed to copy EGO service profiles.",
                     egoServiceConfDir)

