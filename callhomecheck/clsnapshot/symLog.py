import sys
import os
from glob import iglob
import util
from D_Collect import Data_Collect
import socket
import tempfile
import imp
import configfile


def save(path='/tmp'):
    logger = util.getLogger(__name__)
    hosts = set()
    egoConfDir = os.getenv('EGO_CONFDIR')
    if not egoConfDir:
        logger.error('Could not determine the EGO conf directory. Failed to collect EGO log files.')
        return

    egoConfFile = os.path.join(egoConfDir, 'ego.conf')
    if os.path.isfile(egoConfFile):
        config = configfile.getConfigFromFile(egoConfFile)
    else:
        logger.error("Could not find ego.conf. Failed to collect EGO log files. ")
        return

    logger.debug(config.get('EGO_MASTER_LIST', ''))
    for candidate in config.get('EGO_MASTER_LIST', '').strip('"').split():
        if candidate:
            hosts.add(socket.getfqdn(candidate))

    symDC = Data_Collect(path, __name__)
    out = symDC.runit('egosh rg ManagementHosts')
    if out:
        for line in out.splitlines():
            if line.startswith('Resource List:'):
                for host in line.split(':', 1)[-1].split():
                    hosts.add(socket.getfqdn(host))
                break

    tempFolder = tempfile.mkdtemp(prefix='lc_')

    args = [os.path.join(sys.path[0], 'log_collector.py'), 'deploy', tempFolder, " ".join(hosts), 'soam']
    log_collector = imp.load_source(__name__ + '.log_collector',
                                    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log_collector.py'))
    log_collector.main(args)
    logger.debug(os.path.join(tempFolder, '*.sym.logs.*.tar.gz'))
    for fname in iglob(os.path.join(tempFolder, '*.sym.logs.*.tar.gz')):
        symDC.moveit(fname)
    util.rmtree(tempFolder)
