import sys
import os
from glob import iglob
import util
from D_Collect import Data_Collect
import socket
import tempfile
import imp


def save(config, lsfConfig, path='/tmp'):
    logger = util.getLogger(__name__)

    if 'LSF_LOGDIR' in lsfConfig:
        logDir = lsfConfig.get('LSF_LOGDIR', '')
        if os.path.isdir(logDir):
            lsfDC = Data_Collect(path, __name__)
            tempFolder = tempfile.mkdtemp(prefix='lc_')
            args = [os.path.join(sys.path[0], 'log_collector.py'), 'deploy', tempFolder, socket.gethostname(), 'lsf']
            log_collector = imp.load_source(__name__ + '.log_collector',
                                            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                         'log_collector.py'))
            log_collector.main(args)
            for fname in iglob(os.path.join(tempFolder, '*.lsf.logs.*.tar.gz')):
                lsfDC.moveit(fname)
            util.rmtree(tempFolder)
        else:
            logger.error("LSF_LOGDIR directory '%s' does not exist.", logDir)
    else:
        logger.warn('LSF_LOGDIR is not set in lsf.conf. No logs will be collected.')
