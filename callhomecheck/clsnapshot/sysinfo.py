from D_Collect import Data_Collect
from util import getLogger

Sys_Tasks = ['uname -a',
             'uptime',
             'dmesg',
             'top -a -n 1',
             'vmstat -w -t',
             'cat /proc/meminfo',
             'df -h',
             'iostat -t -m',
             'netstat -a -n -p',
             'lsof -u root'
             ]


def save(config, lsfConfig, path='/tmp/'):
    logger = getLogger(__name__)
    sysDataCollector = Data_Collect(path, __name__)
    for syscmd in Sys_Tasks:
        logger.debug("Calling %s ..." % syscmd)
        sysDataCollector.saveit(syscmd)
