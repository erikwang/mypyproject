from D_Collect import Data_Collect
import util

appTasks = ['soamview app "%s" -l',
            'soamview resource "%s" -a',
            'soamview rg "%s" -a',
            'soamview service "%s"'
            ]

symTasks = ['soamview app',
            'sd -V',
            'ssm -V',
            'sim -V',
            ]


def save(path='/tmp'):
    logger = util.getLogger(__name__)
    symDC = Data_Collect(path, __name__)
    output = symDC.runit('soamview app -s enabled')

    if output:
        lines = output.splitlines()
        if lines[0].startswith('APPLICATION'):
            lines.pop(0)
            for line in lines:
                app = line.split()[0]
                for task in appTasks:
                    symTasks.append(task % app)

    for cmd in symTasks:
        logger.debug("Calling %s ..." % cmd)
        symDC.saveit(cmd)
