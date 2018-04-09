from D_Collect import Data_Collect
import util


egoTasks = ['egosh ego info',
            'egosh alloc list -l',
            'egosh alloc view',
            'egosh rg -l',
            'egosh activity list -l',
            'egosh activity view',
            'egosh consumer view -l',
            'egosh resource list -l',
            'egosh resource view',
            'egosh client view',
            'egosh service list -l',
            'egosh service view',
            'egosh entitlement info',
            'lim -V',
            'vemkd -V',
            'egosc -V',
            'pem -V'
            ]


def save(path='/tmp'):
    logger = util.getLogger(__name__)
    egoDC = Data_Collect(path, __name__)
    for cmd in egoTasks:
        logger.debug("Calling %s ..." % cmd)
        egoDC.saveit(cmd)
