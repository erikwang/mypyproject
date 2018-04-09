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
    egoConfDir = os.getenv('EGO_CONFDIR','')
    if not egoConfDir:
        logger.error('Could not determine the EGO conf directory. Failed to collect Symphony log files.')
        return
    egoConfFile = os.path.join(egoConfDir, 'ego.conf')
    if not os.path.isfile(egoConfFile):
        logger.error("Could not find ego.conf. Failed to collect Symphony log files.")
        return
    config = configfile.getConfigFromFile(egoConfFile)
    try:
        for candidate in config['EGO_MASTER_LIST'].strip('"').split():
            hosts.add(socket.getfqdn(candidate))
    except:
        pass

    egoDC = Data_Collect(path, __name__)
    out = egoDC.runit('egosh rg ManagementHosts')
    if out:
        for line in out.splitlines():
            if line.startswith('Resource List:'):
                for host in line.split(':', 1)[-1].split():
                    hosts.add(socket.getfqdn(host))
                break

    tempFolder = tempfile.mkdtemp(prefix='lc_')
    hostList = ' '.join(hosts)
    args = [os.path.join(sys.path[0], 'log_collector.py'), 'deploy', tempFolder, hostList, 'ego']
    log_collector = imp.load_source(__name__ + '.log_collector',
                                    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log_collector.py'))
    log_collector.main(args)
    for filePattern in iglob(os.path.join(tempFolder, '*.ego.logs.*.tar.gz')):
        egoDC.moveit(filePattern)
    util.rmtree(tempFolder)
