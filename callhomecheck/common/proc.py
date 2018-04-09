import psutil
import os
import shlex


def getDaemonProcess(fullPath, parameterFilter=None, returnAllMatches=False):
    procList = []
    parameterFilterList = []
    if parameterFilter:
        parameterFilterList = shlex.split(parameterFilter)
    for proc in psutil.process_iter():
        try:
            if proc.name() != proc.parent().name() and os.path.samefile(proc.exe(), fullPath) and \
                    containsSublist(proc.cmdline()[1:], parameterFilterList):
                if returnAllMatches:
                    procList += [proc]
                else:
                    return proc
        except:
            continue
    if len(procList) > 0:
        return procList
    return None


def containsSublist(searchList, subList):
    if not (isinstance(searchList, list) and isinstance(subList, list)):
        return False
    if not subList:
        return True

    subListLength = len(subList)
    searchListLength = len(searchList)
    if subListLength > searchListLength:
        return False
    for i in range(0, searchListLength - subListLength + 1):
        if searchList[i:i+subListLength] == subList:
            return True
    return False


def kill_with_children(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()