import os
from D_Collect import Data_Collect
import util

Conf_File = "snapshot.conf"


def save(config, lsfConfig, path='/tmp'):

    logger = util.getLogger(__name__)

    if 'LSB_SHAREDIR' not in lsfConfig:
        logger.error("LSB_SHAREDIR is not defined in lsf.conf!")
        return False
    lsfShareDir=lsfConfig['LSB_SHAREDIR']
    lsfData = Data_Collect(path, __name__)
    lsid_out = lsfData.runit('lsid')
    ClName = ''
    for line in lsid_out.splitlines():
        if "My cluster name is" in line:
            ClName = line.split(' ')[4]
            break
    if not ClName:
        logger.error("No cluster can be found!")
        return False
    lsfWorkDir = os.path.join(lsfShareDir, ClName, 'logdir')

    eventNum = config.get('EVENTS_NUM', 0)
    if eventNum:
        eventNum = int(eventNum)
    else:
        eventNum = 0
    lsfData.copyit(os.path.join(lsfWorkDir, 'lsb.events'), 'work/')
    i = 0
    while i < eventNum:
        i += 1
        lsfData.copyit(os.path.join(lsfWorkDir, 'lsb.events' + '.' + str(i)), 'work/')

    lsfData.copyit(os.path.join(lsfWorkDir, 'lsb.acct'), 'work/')
