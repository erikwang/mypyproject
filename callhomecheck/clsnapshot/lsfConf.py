from glob import iglob
from D_Collect import Data_Collect
import util


def save(config, lsfConfig, path='/tmp'):
    logger = util.getLogger(__name__)

    lsfConfCp = Data_Collect(path, __name__)
    lsfConfDir = lsfConfig.get('LSF_CONFDIR', '')
    if lsfConfDir:
        lsfConfCp.copyit(lsfConfig['LSF_CONFDIR'])
    else:
        logger.error("Could not determine the LSF configuration dir. Failed to collect LSF configuration files.")
    lsfConfCp.copyit('/etc/lsf.sudoers')
    for fname in iglob('/etc/init.d/*lsf*'):
        lsfConfCp.copyit(fname, 'initd/')
