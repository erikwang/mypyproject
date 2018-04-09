import logging
import os
import sys
import socket
import time
import ConfigParser
import StringIO
import re
import tarfile
import pipes
import getpass
import threading
from stat import S_ISDIR

egoLogs = ['lim', 'pem', 'vemkd', 'sd', 'ssm']
soamLogs = ['sd', 'ssm']
lsfLogs = ['mbatchd', 'sbatchd', 'mbschd']
logger = None
threadLock = threading.Lock()


def rm(sftp, path):
    global logger
    files = sftp.listdir(path)

    for f in files:
        filepath = os.path.join(path, f)
        try:
            sftp.remove(filepath)
        except IOError:
            if S_ISDIR(sftp.stat(filepath).st_mode):
                rm(sftp, filepath)
            else:
                logger.exception("Could not clean up %s.", filepath)
    try:
        sftp.rmdir(path)
    except IOError:
        logger.exception("Could not clean up %s.", path)


def getLogger(name):
    if name == '__main__':
        return logging.getLogger(BaseLoggerName)
    else:
        return logging.getLogger(BaseLoggerName + "." + name)


# Collect logs generated from this host.
def collectInfo(logDir, tarFilePath, component):
    global logger
    global threadLock

    if component == 'ego':
        fileRegex = '^%s\\.log\\.%s(\\.[1-9]+[0-9]*)?$' \
                    % (listToRegex(egoLogs), listToRegex([socket.gethostname(), socket.getfqdn()]))
    elif component == 'soam':
        hostNameRegex = listToRegex([socket.gethostname(), socket.getfqdn()])
        fileRegex = '^(sd\\.%s\\.log(\\.[1-9]+[0-9]*)?|ssm\\.%s\\..+\\.log(\\.[1-9]+[0-9]*)?)$'\
                    % (hostNameRegex, hostNameRegex)
    elif component == 'lsf':
        fileRegex = '^%s\\.log\\.%s(\\.[1-9]+[0-9]*)?$' \
                    % (listToRegex(lsfLogs), listToRegex([socket.gethostname(), socket.getfqdn()]))
    else:
        return

    logger.info("Creating archive %s", tarFilePath)
    tar = None
    with threadLock:
        cwd = os.getcwd()
        os.chdir(os.path.dirname(tarFilePath))
        tar = tarfile.open(os.path.basename(tarFilePath), "w:gz")
        os.chdir(cwd)
    if tar:
        pattern = re.compile(fileRegex)
        for f in filter(pattern.match, os.listdir(logDir)):
            tar.add(os.path.join(logDir, f), arcname=f)
        tar.close()


# Helper turns a list ['a.1','b.1','c.1'] into regex (a\\.1|b\\.1|c\\.1)
def listToRegex(fList):
    regex = '('
    for item in fList:
        regex = regex + re.escape(item) + '|'
    regex = regex.rstrip('|') + ')'
    return regex


# Reads a platform conf file and returns a config parser with paramaters under section '[root]'
def getConfig(filePath):
    cp = ConfigParser.ConfigParser()
    try:
        config = StringIO.StringIO()
        config.write('[root]\n')
        config.write(open(filePath).read())
        config.seek(0, os.SEEK_SET)
        cp.readfp(config)
    finally:
        return cp


def sshToHost(host, egoLogDir, soamLogDir, lsfLogDir, filenameEgo, filenameSoam, filenameLsf, outputDir,
              data, pKeyFile=None):
    import paramiko
    global logger
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    client.load_system_host_keys()

    host = socket.getfqdn(host)
    cfg = {'hostname': host, 'username': getpass.getuser()}

    if pKeyFile:
        cfg['pkey'] = paramiko.RSAKey.from_private_key_file(pKeyFile)
    elif os.path.isfile(os.getenv('SSH_PRIVATE_KEY', '')):
        logger.debug(os.getenv('SSH_PRIVATE_KEY', ''))
        cfg['pkey'] = paramiko.RSAKey.from_private_key_file(os.getenv('SSH_PRIVATE_KEY', ''))
    else:
        ssh_config = paramiko.SSHConfig()
        user_config_file = os.path.expanduser("~/.ssh/config")
        if os.path.exists(user_config_file):
            with open(user_config_file) as f:
                ssh_config.parse(f)
        user_config = ssh_config.lookup(cfg['hostname'])
        for k in ('hostname', 'username', 'port'):
            if k in user_config:
                cfg[k] = user_config[k]

        if 'identityfile' in user_config:
            cfg['key_filename'] = user_config['identityfile']
        if 'proxycommand' in user_config:
            cfg['sock'] = paramiko.ProxyCommand(user_config['proxycommand'])

    logger.info("Connecting to host %s" % host)
    try:
        # client.connect(host)
        client.connect(**cfg)
    except paramiko.AuthenticationException:
        logger.exception("Authentication failed connecting to host %s", host)
        return False
    except socket.error as e:
        logger.exception("Could not connect to host %s. %d:%s" % (host, e.errno, os.strerror(e.errno)))
        return False
    except paramiko.BadHostKeyException:
        logger.exception("Failed connecting to host %s. Bad host key.", host)
        return False
    except paramiko.SSHException:
        logger.exception("Failed connecting to host %s. SSH failure.", host)
        return False
    # Setup sftp connection and transmit this script
    sftp = client.open_sftp()

    command = 'mktemp -d'

    try:
        stdin, stdout, stderr = client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status:
            logger.error("Command to make a temporary directory on host %s failed.", host)
            return False
        remoteFolder = stdout.readlines()[0].strip()
        if not remoteFolder:
            logger.error("Unable to get the temporary directory on host %s.", host)
            return False
    except paramiko.SSHException:
        logger.exception("Could not execute the command to create a temporary directory on host %s.", host)
        return False

    failed = False

    remoteScript = os.path.join(remoteFolder, 'log_collector.py')
    try:
        sftp.put(os.path.abspath(__file__), remoteScript)
    except OSError:
        logger.exception("Could not put %s on host %s.", remoteScript, host)
        failed = True

    if not failed:
        command = 'python -B %s collect %s %s %s %s %s %s %s %s' \
                  % (pipes.quote(remoteScript), pipes.quote(egoLogDir), pipes.quote(soamLogDir), pipes.quote(lsfLogDir),
                     pipes.quote(filenameEgo), pipes.quote(filenameSoam), pipes.quote(filenameLsf), pipes.quote(data),
                     pipes.quote(remoteFolder))
        try:
            stdin, stdout, stderr = client.exec_command(command)
        except paramiko.SSHException:
            failed = True
            logger.exception("Unable to execute %s on host %s.", remoteScript, host)

    if not failed:
        exit_status = stdout.channel.recv_exit_status()
        if exit_status:
            failed = True
            logger.error("Script %s exited with exit code %d on host %s.", remoteScript, exit_status, host)

    files = []
    if not failed:
        try:
            files = sftp.listdir(remoteFolder)
        except OSError:
            failed = True
            logger.exception("Unable to list contents of %s on host %s.", remoteFolder, host)

    if not failed:
        if filenameEgo in files:
            try:
                sftp.get(os.path.join(remoteFolder, filenameEgo), os.path.join(outputDir, filenameEgo))
            except IOError:
                failed = True
                logger.exception("Error getting EGO log files from host %s.", host)
        if filenameSoam in files:
            try:
                sftp.get(os.path.join(remoteFolder, filenameSoam), os.path.join(outputDir, filenameSoam))
            except IOError:
                failed = True
                logger.exception("Error getting SYM log files from host %s.", host)
        if filenameLsf in files:
            try:
                sftp.get(os.path.join(remoteFolder, filenameLsf), os.path.join(outputDir, filenameLsf))
            except IOError:
                failed = True
                logger.exception("Error getting LSF log files from host %s.", host)

    rm(sftp, remoteFolder)
    sftp.close()
    return not failed


def main(argv=None):
    global logger
    isModule = False
    logger = getLogger(__name__)
    if argv:
        isModule = True
    else:
        argv = sys.argv
        formatter = logging.Formatter('%(message)s')
        sHandle = logging.StreamHandler(sys.stdout)
        sHandle.setFormatter(formatter)
        sHandle.setLevel(logging.INFO)
        logger.setLevel(logging.NOTSET)
        logger.addHandler(sHandle)
    logging.getLogger("paramiko").setLevel(logging.NOTSET)

    if len(argv) < 4:
        logging.info("Not enough arguments provided. Please provide mode, path, hosts and information to be collected"
                     " in the following format: log_collector deploy /tmp host1 host2 sym ego")
    else:
        try:
            if argv[1] == 'deploy':
                #  Data to collect
                data = argv[4]
                logger.info("Data to collect: %s." % data)

                #  Parse the ego.conf file and get the master list
                masterHostList = argv[3].split()
                # masterHostList = egoSharedConf.get('root','EGO_MASTER_LIST').replace("\"","").split()
                egoConfig = None
                lsfConfig = None

                egoConfDir = os.getenv('EGO_CONFDIR')
                lsfConfDir = os.getenv('LSF_ENVDIR')
                if egoConfDir and os.path.isdir(egoConfDir):
                    egoConfFile = os.path.join(egoConfDir, 'ego.conf')
                    egoConfig = getConfig(egoConfFile)
                if lsfConfDir and os.path.isdir(lsfConfDir):
                    lsfConfFile = os.path.join(lsfConfDir, 'lsf.conf')
                    lsfConfig = getConfig(lsfConfFile)

                if len(masterHostList) == 0:
                    if egoConfig and egoConfig.has_option('root', 'EGO_MASTER_LIST'):
                        masterHostList = egoConfig.get('EGO_MASTER_LIST', '').split()
                    elif lsfConfig and lsfConfig.has_option('root', 'LSF_MASTER_LIST'):
                        masterHostList = lsfConfig.get('LSF_MASTER_LIST', '').split()
                logger.info("Master host list is %s.", ', '.join(masterHostList))

                dataList = data.split()
                #  Get EGO_LOGDIR
                egoLogDir = ''
                if 'ego' in dataList and egoConfig and egoConfig.has_option('root', 'EGO_LOGDIR'):
                    egoLogDir = egoConfig.get('root', 'EGO_LOGDIR')
                    logger.info("EGO log directory is  %s.", egoLogDir)

                #  Construct soam log directory from SOAM_HOME
                soamLogDir = ''
                if 'soam' in dataList and os.getenv('SOAM_HOME'):
                    soamLogDir = os.path.join(os.getenv('SOAM_HOME'), 'logs/')
                    logger.info("SOAM log directory is  %s.", soamLogDir)

                #  Get LSF_LOGDIR
                lsfLogDir = ''
                if 'lsf' in dataList and lsfConfig and lsfConfig.has_option('root', 'LSF_LOGDIR'):
                    lsfLogDir = lsfConfig.get('root', 'LSF_LOGDIR')
                    logger.info("LSF log directory is  %s.", lsfLogDir)

                #  Get current directory
                # currDir = os.path.dirname(os.path.realpath(__file__))
                # logger.info("Current directory is  %s." % currDir)

                #  Get output directory
                outputDir = argv[2]
                logger.info("Output directory is %s.", outputDir)

                #  SSH on each host and collect the EGO and SOAM logs
                for host in masterHostList:
                    timeStamp = time.strftime("%Y%m%d-%H%M%S")
                    filenameEGO = host + '.ego.logs.' + timeStamp + '.tar.gz'
                    filenameSOAM = host + '.sym.logs.' + timeStamp + '.tar.gz'
                    filenameLSF = host + '.lsf.logs.' + timeStamp + '.tar.gz'
                    if socket.getfqdn(host) == socket.getfqdn():
                        if 'ego' in dataList:
                            collectInfo(egoLogDir, os.path.join(outputDir, filenameEGO), 'ego')
                        if 'soam' in dataList:
                            collectInfo(soamLogDir, os.path.join(outputDir, filenameSOAM), 'soam')
                        if 'lsf' in dataList:
                            collectInfo(lsfLogDir, os.path.join(outputDir, filenameLSF), 'lsf')
                    else:
                        sshToHost(host, egoLogDir, soamLogDir, lsfLogDir, filenameEGO, filenameSOAM, filenameLSF,
                                  outputDir, data)

            elif sys.argv[1] == 'collect':

                # Construct EGO and SOAM log file locations from second argument which is EGO_LOCALDIR
                egoLogDir = argv[2]
                soamLogDir = argv[3]
                lsfLogDir = argv[4]
                filenameEgo = argv[5]
                filenameSoam = argv[6]
                filenameLsf = argv[7]
                data = argv[8].split()
                tempFolder = argv[9]

                # Collect ego log files
                if 'ego' in data:
                    tarPath = os.path.join(tempFolder, filenameEgo)
                    collectInfo(egoLogDir, tarPath, 'ego')
                # Collect soam log files
                if 'soam' in data:
                    tarPath = os.path.join(tempFolder, filenameSoam)
                    collectInfo(soamLogDir, tarPath, 'soam')
                # Collect lsf log files
                if 'lsf' in data:
                    tarPath = os.path.join(tempFolder, filenameLsf)
                    collectInfo(lsfLogDir, tarPath, 'lsf')

        except IndexError:
            pass
    if not isModule:
        exit(0)
    else:
        return 0


BaseLoggerName = os.path.splitext(os.path.basename(sys.argv[0]))[0]
logging.addLevelName(logging.CRITICAL, 'CRIT')
logging.addLevelName(logging.WARNING, 'WARN')
if __name__ == "__main__":
    main(None)
