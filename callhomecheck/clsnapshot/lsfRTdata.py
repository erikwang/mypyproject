from D_Collect import Data_Collect
import util

Conf_File = "snapshot.conf"
lsfSnapCommands = ['lsid', 'lshosts -w', 'lshosts -l', 'lsclusters', 'bhosts -w', 'bhosts -l', 'bhosts -s', 'bjobs -w',
                   'bjobs -l', 'bqueues -w', 'bqueues -l', 'bparams -a', 'bresources', 'blimits', 'blusers', 'blstat',
                   'blhosts', 'blinfo']


def save(config, lsfConfig, path='/tmp'):
    logger = util.getLogger(__name__)
    lsfsim = Data_Collect(path, __name__)
    for command in lsfSnapCommands:
        logger.debug("Calling %s ..." % command)
        lsfsim.saveit(command)
