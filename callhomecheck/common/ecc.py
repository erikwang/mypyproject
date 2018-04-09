import logging
import util
import os.path
import socket
import getpass
from log import getLogger
from util import isLocalHost

eccFileDir = '/tmp/.ecc_files/'


def parseFileUploadedLine(line):
    if line.startswith('Upload callback- File ') and line.endswith(' has been uploaded'):
        return line[22:-18]
    return ''


def testECCClient(eccConfig):
    logger = getLogger(__name__)
    logger.info("Test running the ECC client...")
    cmd = ['java', '-jar', os.path.join(eccConfig['ECC_TOP'], eccConfig['ECC_JAR'])]
    if eccConfig['ECC_JAVA_HOME']:
        cmd[0] = os.path.join(eccConfig['ECC_JAVA_HOME'], 'bin', 'java')
    cmd += ['-V']
    if logger.getEffectiveLevel() == logging.DEBUG:
        cmd += ['-d', 'true']

    if isLocalHost(eccConfig['ECC_HOST']):
        finished, stdout, stderr, returncode = util.runCommandStdOutErrCode(cmd, eccConfig['ECC_TIMEOUT'])
    else:
        finished, stdout, stderr, returncode = util.runRemoteCommandStdOutErrCode(eccConfig['ECC_HOST'], cmd,
                                                                                  eccConfig['ECC_TIMEOUT'])

    logger.debug('ECC client exit code %d. Command output: %s', returncode, stdout)
    if not finished:
        logger.error("The ECC client test did not finish after the configured timeout of %d seconds.",
                     eccConfig['ECC_TIMEOUT'])
        return False
    elif returncode:
        logger.error("The ECC client did not run successfully. The client exited with exit code %d and the following"
                     " output:", returncode)
        logger.error(stdout.strip())
        return False
    else:
        logger.info("The ECC client was able to run successfully.")
    return True


def createPMR(component, version, summary, body, eccConfig, files=None):
    summary = eccConfig['SUMMARY_PREFIX'] + " " + summary.lstrip()
    return createPMRHelper(eccConfig['ECC_JAR'], eccConfig['ECC_TOP'], component, version, eccConfig['ICN'],
                           eccConfig['UUID'], eccConfig['CUSTOMER_NAME'], eccConfig['GROUP'], eccConfig['PHONE'],
                           eccConfig['EMAIL'],  eccConfig['CITY'],  eccConfig['COUNTRY'], eccConfig['SEVERITY'],
                           summary, body, eccConfig['ECC_TIMEOUT'], files, eccConfig['ECC_JAVA_HOME'],
                           eccConfig['ECC_HOST'])


def createPMRHelper(eccJar, eccTop, component, version, icn, uuid, contactName, group, phone, email, city, country,
                    severity, summary, body, timeout=300, files=None, javaHome='', eccHost=None):
    logger = getLogger(__name__)

    if not files:
        files = []
    if eccHost and isLocalHost(eccHost):
        eccHost = None
    if eccHost and files:
        files = copyFilesToECCHost(eccHost, files)
        if not files:
            logger.error("Could not copy snapshot files to host %s for upload to PMR.", eccHost)

    logger.info("Creating PMR...")
    cmd = ['java', '-jar',  os.path.join(eccTop, eccJar)]
    if javaHome:
        cmd[0] = os.path.join(javaHome, 'bin', 'java')
    cmd += ['-E', os.path.join(eccTop, 'ecchome')]
    cmd += ['-i', component]
    cmd += ['-v', version]
    cmd += ['-I', icn]
    cmd += ['-u', uuid]
    cmd += ['-N', contactName]
    cmd += ['-F', group]
    cmd += ['-p', phone]
    cmd += ['-s', str(severity)]
    cmd += ['-c', city]
    cmd += ['-C', country]
    cmd += ['-T', summary]
    cmd += ['-t', body]
    cmd += ['-e', email]
    if files:
        cmd += ['-U', ';'.join(files)]
    if logger.getEffectiveLevel() == logging.DEBUG:
        cmd += ['-d', 'true']

    logger.info('Calling ECC client to generate PMR...')
    logger.debug('ECC command: %s', cmd)
    if eccHost:
        finished, stdout, stderr, returncode = util.runRemoteCommandStdOutErrCode(eccHost, cmd, timeout)
    else:
        finished, stdout, stderr, returncode = util.runCommandStdOutErrCode(cmd, timeout)
    logger.debug('ECC client exit code %d. Command output: %s', returncode, stdout)
    if not finished:
        logger.warn("The ECC client did not finish after the configured timeout of %d seconds.", timeout)
    elif returncode:
        logger.warn("The ECC client exited with exit code %d.", returncode)
    logger.debug('ECC stdout: %s, ECC stderr: %s', stdout, stderr)

    if eccHost and files:
        cleanFilesOnECCHost(files, eccHost)

    pmrNumber = ''
    uploadedFiles = []
    srid = ''
    uri = ''

    for line in stdout.splitlines():
        if line.startswith('PMR ID ='):
            pmrNumber = line.split('=', 1)[-1].strip()
            logger.info('Successfully created PMR#%s', pmrNumber)
        elif line.startswith('srid ='):
            srid = line.split('=', 1)[-1].strip()
        elif line.startswith('uri ='):
            uri = line.split('=', 1)[-1].strip()
            logger.info('The PMR uri is %s', uri)
        elif line.startswith('Description ='):
            if line.split('=', 1)[-1].strip().startswith('This request was detected as a Duplicate'):
                logger.warn('This request was detected as a duplicate PMR.')
        elif files:
            f = parseFileUploadedLine(line)
            if f:
                uploadedFiles.append(f)
                logger.info('File %s successfully uploaded to the PMR', f)

    if len(pmrNumber) == 11:
        pmrNumber = "%s,%s,%s" % (pmrNumber[0:5], pmrNumber[5:8], pmrNumber[8:11])
    if not pmrNumber:
        logger.error('Failed to generate PMR.')
    if len(uploadedFiles) < len(files):
        logger.error('Failed to upload all files')

    return pmrNumber, srid, uploadedFiles, uri


def uploadFilesToPMR(uri, files, eccConfig):
    return uploadFilesToPMRHelper(eccConfig['ECC_JAR'], eccConfig['ECC_TOP'], eccConfig['GROUP'], uri, files,
                                  eccConfig['ECC_TIMEOUT'], eccConfig['ECC_JAVA_HOME'], eccConfig['ECC_HOST'])


def uploadFilesToPMRHelper(eccJar, eccTop, group, uri, files, timeout=300, javaHome='', eccHost=None):
    logger = getLogger(__name__)

    if eccHost and isLocalHost(eccHost):
        eccHost = None

    if eccHost and files:
        files = copyFilesToECCHost(eccHost, files)
        if not files:
            logger.error("Could not copy snapshot files to host %s for upload to PMR.", eccHost)
            return None
    elif not files:
        logger.error("No files give for upload to the PMR.")
        return None

    cmd = ['java', '-jar', os.path.join(eccTop, eccJar)]
    if javaHome:
        cmd[0] = os.path.join(javaHome, 'bin', 'java')
    cmd += ['-E', os.path.join(eccTop, 'ecchome'), '-F', group, '-U', ';'.join(files), '-r', uri]
    if logger.getEffectiveLevel() == logging.DEBUG:
        cmd += ['-d', 'true']

    logger.info('Calling ECC client to upload file(s) to the PMR...')
    if eccHost:
        finished, stdout, stderr, returncode = util.runRemoteCommandStdOutErrCode(eccHost, cmd, timeout)
    else:
        finished, stdout, stderr, returncode = util.runCommandStdOutErrCode(cmd, timeout)

    logger.debug('ECC client exit code %d. Command output: %s', returncode, stdout)
    if not finished:
        logger.warn("The ECC client did not finish after the configured timeout of %d seconds.", timeout)
    elif returncode:
        logger.warn("The ECC client exited with exit code %d.", returncode)
    logger.debug('ECC stdout: %s, ECC stderr: %s', stdout, stderr)

    if eccHost and files:
        cleanFilesOnECCHost(files, eccHost)

    uploadedFiles = []
    for line in stdout.splitlines():
        f = parseFileUploadedLine(line)
        if f:
            uploadedFiles.append(f)
            logger.info('File %s successfully uploaded to the PMR.', f)

    if len(uploadedFiles) < len(files):
        logger.error('Failed to upload all files.')

    return uploadedFiles


def copyFilesToECCHost(host, files):
    import paramiko
    logger = getLogger(__name__)
    filesUploaded = []
    if len(files) < 1:
        return filesUploaded

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()

    ssh_config = paramiko.SSHConfig()
    user_config_file = os.path.expanduser("~/.ssh/config")
    if os.path.exists(user_config_file):
        with open(user_config_file) as f:
            ssh_config.parse(f)
    host = socket.getfqdn(host)
    cfg = {'hostname': host, 'username': getpass.getuser()}
    user_config = ssh_config.lookup(cfg['hostname'])
    for k in ('hostname', 'username', 'port'):
        if k in user_config:
            cfg[k] = user_config[k]

    if 'identityfile' in user_config:
        cfg['key_filename'] = user_config['identityfile']
    if 'proxycommand' in user_config:
        cfg['sock'] = paramiko.ProxyCommand(user_config['proxycommand'])

    logger.info("Connecting to host %s", host)
    try:
        client.connect(**cfg)
    except paramiko.SSHException:
        logger.exception("Could not connect to host %s.", host)
        return filesUploaded
    except socket.error as e:
        logger.exception("Could not connect to host %s. %d:%s", host, e.errno, os.strerror(e.errno))
        return filesUploaded

    # Setup sftp connection and transmit this script
    sftp = client.open_sftp()

    try:
        sftp.chdir(eccFileDir)  # Test if remote_path exists
    except IOError:
        try:
            sftp.mkdir(eccFileDir)  # Create remote_path
        except IOError:
            logger.error("Could not make directory '%s' on host %s.", eccFileDir, host)
            sftp.close()
            client.close()
            return filesUploaded

    for f in files:
        destination = os.path.join(eccFileDir, os.path.basename(f))
        try:
            sftp.put(f, destination)
        except IOError:
            logger.exception("Could not upload '%s' to %s on host %s.", f, destination, host)
            continue
        filesUploaded.append(destination)

    sftp.close()
    client.close()
    return filesUploaded


def cleanFilesOnECCHost(files, host):
    import paramiko
    logger = getLogger(__name__)
    filesUploaded = []
    if len(files) < 1:
        return filesUploaded

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()

    ssh_config = paramiko.SSHConfig()
    user_config_file = os.path.expanduser("~/.ssh/config")
    if os.path.exists(user_config_file):
        with open(user_config_file) as f:
            ssh_config.parse(f)
    host = socket.getfqdn(host)
    cfg = {'hostname': host, 'username': getpass.getuser()}
    user_config = ssh_config.lookup(cfg['hostname'])
    for k in ('hostname', 'username', 'port'):
        if k in user_config:
            cfg[k] = user_config[k]

    if 'identityfile' in user_config:
        cfg['key_filename'] = user_config['identityfile']
    if 'proxycommand' in user_config:
        cfg['sock'] = paramiko.ProxyCommand(user_config['proxycommand'])

    logger.info("Connecting to host %s", host)
    try:
        client.connect(**cfg)
    except EnvironmentError as e:
        logger.error("Could not connect to host %s. %d:%s", host, e.errno, os.strerror(e.errno))
        return filesUploaded
    # Setup sftp connection and transmit this script
    sftp = client.open_sftp()

    for f in files:
        f = os.path.join(eccFileDir, os.path.basename(f))
        try:
            sftp.remove(f)
        except Exception:
            logger.exception("Could not delete '%s' on host %s.", f, host)
            continue
    try:
        dirFiles = sftp.listdir(eccFileDir)
        if dirFiles and len(dirFiles) == 0:
            sftp.rmdir(eccFileDir)
    except Exception:
        logger.exception("Could not delete directory '%s' on host %s.", eccFileDir, host)
