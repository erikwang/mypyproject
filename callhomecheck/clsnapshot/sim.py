import os
from D_Collect import Data_Collect
import util
import tempfile


def save(config, lsfConfig, path='/tmp'):
    logger = util.getLogger(__name__)

    logger.debug("Getting lshosts/lsload data for Simulator ...")
    lsfCommand = Data_Collect(path, __name__)
    lshosts_out = lsfCommand.runit('lshosts -l')
    if lshosts_out is None:
        logger.error("Failed running 'lshosts -l'. Failed to collect LSF sim data.")
        return
    lsload_out = lsfCommand.runit('lsload -w')
    if lsload_out is None:
        logger.error("Failed running 'lsload -w'. Failed to collect LSF sim data.")
        return
    # hostname type model maxmem maxswp maxtmp ndisks nprocs ncores nthreads 
    # r15s r1m r15m ut pg ls it tmp swp mem
    # print("".join([s for s in lshosts_out.strip().splitlines(True) if s.strip()]))
    # print("".join([s for s in lsload_out.strip().splitlines(True) if s.strip()]))
    htrace = dict()
    lshosts_idx = {'type': 0, 'model': 1, 'maxmem': 2, 'maxswp': 3, 'maxtmp': 4, 'ndisks': 5, 'nprocs': 6, 'ncores': 7,
                   'nthreads': 8}
    # lsload_idx = {'r15s': 0, 'r1m': 1, 'r15m': 2, 'ut': 3, 'pg': 4, 'ls': 5, 'it': 6, 'tmp': 7, 'swp': 8, 'mem': 9}
    htrace_rec = ['UNKNOWN_AUTO_DETECT', 'UNKNOWN_AUTO_DETECT', '0M', '0M', '0M', '0', '0', '0', '0',
                  '-', '-', '-', '-', '-', '-', '-', '-', '-', '-']

    lines = lshosts_out.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith('HOST_NAME:'):
            k_hname = lines[i].split()[1]
            htrace[k_hname] = list(htrace_rec)
            lineList = lines[i + 2].split()
            for j in range(len(lineList)):
                if j == 0:
                    if lineList[j] != '-':
                        htrace[k_hname][lshosts_idx['type']] = lineList[j]
                elif j == 1:
                    if lineList[j] != '-':
                        htrace[k_hname][lshosts_idx['model']] = lineList[j]
                elif j == 2 or j == 3:
                    pass  # skip cpuf, ncpus
                elif j == 4:
                    if lineList[j] != '-':
                        htrace[k_hname][lshosts_idx['ndisks']] = lineList[j]
                elif j == 5:
                    if lineList[j] != '-':
                        htrace[k_hname][lshosts_idx['maxmem']] = lineList[j]
                elif j == 6:
                    if lineList[j] != '-':
                        htrace[k_hname][lshosts_idx['maxswp']] = lineList[j]
                elif j == 7:
                    if lineList[j] != '-':
                        htrace[k_hname][lshosts_idx['maxtmp']] = lineList[j]
                elif j == 8 or j == 9:
                    pass  # skip rexpri, server
                elif j == 10:
                    if lineList[j] != '-':
                        htrace[k_hname][lshosts_idx['nprocs']] = lineList[j]
                elif j == 11:
                    if lineList[j] != '-':
                        htrace[k_hname][lshosts_idx['ncores']] = lineList[j]
                elif j == 12:
                    if lineList[j] != '-':
                        htrace[k_hname][lshosts_idx['nthreads']] = lineList[j]
            i += 2
        i += 1

    # pdb.set_trace()
    idx_off = len(lshosts_idx)
    for i, line in enumerate("".join([s for s in lsload_out.strip().splitlines(True) if s.strip()]).splitlines()):
        if i == 0:
            continue  # skip lsload title
        lineList = line.split()
        k_hname = lineList[0]
        # idx_off = len(lshosts_idx)
        for j in range(len(lineList) - 2):
            htrace[k_hname][idx_off + j] = lineList[j + 2]
    tempFile = os.path.join(tempfile.tempdir, 'bsim_htrace_file.%s' % os.getpid())
    outputFile = open(tempFile, 'a')
    outputFile.write('hostname type model maxmem maxswp maxtmp ndisks nprocs ncores nthreads r15s r1m r15m ut pg ls it tmp'
                  ' swp mem\n')
    for h_name in htrace:
        h_load = htrace[h_name]
        outputFile.write(h_name + ' ' + " ".join(h_load) + '\n')
    outputFile.close()

    simData = Data_Collect(path, __name__)
    simData.saveit('cat ' + tempFile)
    os.remove(tempFile)
