from log import getLogger
import re
import subprocess
from email.mime.text import MIMEText
import smtplib


def validateEmailConfig(emailConfig):
    logger = getLogger(__name__)
    if not emailConfig['TO']:
        logger.error('The TO parameter does not define at least one valid e-mail address.')
        exit(-1)
    emailRegex = re.compile(r"[0-9A-Za-z ]+ +\<[^@]+@[^@]+\.[^@]+\>")
    if not emailConfig['FROM']:
        logger.error('The e-mail FROM parameter is not defined.')
        exit(-1)
    elif not emailRegex.match(emailConfig['FROM']):
        logger.error('The e-mail FROM parameter %s is not in the correct format.', emailConfig['FROM'])
        exit(-1)
    emailRegex = re.compile(r"[^@]+@[^@]+\.[^@]+")
    correctEmails = []
    for address in emailConfig['TO']:
        if emailRegex.match(address.strip()):
            correctEmails.append(address.strip())
        else:
            logger.warn("The TO e-mail '%s' is an invalid e-mail address format.", address)
    if not len(correctEmails):
        logger.error("No valid TO e-mail addresses are defined. Exiting.")
        exit(-1)
    emailConfig['TO'] = correctEmails


def sendTestEmail(emailConfig, clusterName):
    logger = getLogger(__name__)
    logger.info('Sending test email...')
    message = createPMREmailMIMEText(emailConfig, ['This is a test e-mail.'], clusterName.name, '')
    if sendEmail(emailConfig, message):
        logger.info('Test Passed. Test email was sent successfully. ')
        exit(0)
    else:
        logger.error('Test Failed. Could not send test email. Please check your email configuration.')
        exit(-1)


def sendEmailProg(program, message):
    logger = getLogger(__name__)
    try:
        proc =\
            subprocess.Popen([program, '-t'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        proc.communicate(input=message.as_string())[0]
        return not proc.returncode
    except OSError:
        logger.exception("Failed to send e-mail.")
    return False


def sendEmailSMTP(server, port, sender, recipientList, message):
    failed = False
    logger = getLogger(__name__)
    conn = smtplib.SMTP(server, port)
    try:
        conn.sendmail(sender, recipientList, message.as_string())
    except Exception:
        logger.exception("Failed to send e-mail.")
        failed = True
    finally:
        conn.quit()
    return not failed


def sendEmail(emailConfig, message):
    if emailConfig['COMMAND']:
        return sendEmailProg(emailConfig['COMMAND'], message)
    else:
        serverParts = emailConfig['EMAIL_SERVER'].split(':')
        server = serverParts[0]
        port = 25
        if len(serverParts) == 2:
            port = int(serverParts[1])
        return sendEmailSMTP(server, port, emailConfig['FROM'], emailConfig['TO'], message)


def createPMREmailMIMEText(emailConfig, errors, clusterName, pmr, generateSnapshot=False, autoUpload=False,
                           commandLine=None):

    listPrefix = '\n- '

    body = ['Electronic Service Agent has detected an event with the following message(s):',
            '%s%s' % (listPrefix, listPrefix.join(errors)), '']
    if pmr.strip():
        body.append('')
        body.append('PMR service request %s has been automatically opened with IBM Support.' % pmr)

        if generateSnapshot and autoUpload:
            body.append('')
            body.append('A cluster snapshot file is being generated and will be automatically be uploaded to the PMR.')
    else:
        body.append('')
        if commandLine:
            body.append('If this is a potential problem, please run the following command to open a PMR service request'
                        ' with IBM Support:')
            body.append('\t%s' % commandLine)
        else:
            body.append('If this is a potential problem, please open a PMR service request with IBM Support.')

    if generateSnapshot and not autoUpload:
        body.append('')
        body.append('A cluster snapshot file is being generated.')

    body.append('')
    body.append('Alert Contact:')
    breakLine = len(body)
    body.append('Name: %s' % emailConfig['CONTACT_NAME'])
    if emailConfig['CONTACT_PHONE']:
        body.append('Phone: %s' % emailConfig['CONTACT_PHONE'])
    if emailConfig['CONTACT_EMAIL']:
        body.append('E-mail: %s' % emailConfig['CONTACT_EMAIL'])

    body.insert(breakLine, '-' * len(max(body[breakLine-1:], key=len)))

    if emailConfig['CUSTOM_MESSAGE']:
        body.append('')
        body += emailConfig['CUSTOM_MESSAGE'].splitlines()
    msg = MIMEText('\n'.join(body), 'plain')
    msg["From"] = emailConfig['FROM']
    msg["To"] = ", ".join(emailConfig['TO'])
    if clusterName:
        msg["Subject"] = '[Call Home] Cluster %s: Potential problem detected %s' % (clusterName, errors[0])
    else:
        msg["Subject"] = '[Call Home] Potential problem detected %s' % errors[0]
    return msg


def createUploadEmailMIMEText(emailConfig, errors, pmr, files, clusterName, uploadCommand, generatedSnapFile=None,
                              autoUpload=False, uploadedFiles=None, failedFiles=None):

    body = list()
    body.append('Snapshot action summary triggered by the following alert:')
    for e in errors:
        body.append('\t%s' % e)

    if generatedSnapFile:
        body.append('')
        body.append("Snapshot file '%s' has been created." % generatedSnapFile)
    elif generatedSnapFile == '':
        body.append('')
        body.append("Cluster Check was unable to generate a snapshot file for this alert. ")

    if pmr:
        if autoUpload:
            if uploadedFiles:
                body.append('')
                body.append('Snapshot files successfully uploaded to PMR#%s:' % pmr)
                for f in uploadedFiles:
                    body.append('\t%s' % f)
            if failedFiles:
                plural = ''
                if len(failedFiles) > 0:
                    plural = 's'
                body.append('')
                body.append('Snapshot file%s failed uploading to PMR#%s:' % (plural, pmr))
                for f in failedFiles:
                    body.append('\t'.join(f))
                body.append('Run the following command to retry uploading the failed snapshot%s to the PMR:' % pmr)
                body.append("\t%s '%s'" % (uploadCommand, "' '".join(failedFiles)))
        else:
            if files:
                plural = ''
                if len(files) > 0:
                    plural = 's'
                body.append('')
                body.append('Run the following command to upload the snapshot%s to PMR#%s:' % (plural, pmr))
                body.append("\t%s '%s'" % (uploadCommand, "' '".join(files)))
        body.append('')
        body.append('Use the following command to upload other files to PMR#%s in the future:' % pmr)
        body.append("\t%s file1 [file2 ...]" % uploadCommand)
    elif generatedSnapFile:
        body.append('')
        body.append("Please upload snapshot file '%s' to the PMR using the IBM ECuRep portal (%s) once a PMR has been"
                    " created for this issue." % (generatedSnapFile, 'https://www.ecurep.ibm.com/app/upload'))

    body.append('')
    body.append('Alert Contact:')
    breakLine = len(body)
    body.append('Name: %s' % emailConfig['CONTACT_NAME'])
    if emailConfig['CONTACT_PHONE']:
        body.append('Phone: %s' % emailConfig['CONTACT_PHONE'])
    if emailConfig['CONTACT_EMAIL']:
        body.append('E-mail: %s' % emailConfig['CONTACT_EMAIL'])
    body.insert(breakLine, '-' * len(max(body[breakLine-1:], key=len)))

    msg = MIMEText('\n'.join(body), 'plain')
    msg["From"] = emailConfig['FROM']
    msg["To"] = ", ".join(emailConfig['TO'])
    if clusterName:
        msg["Subject"] = '[Call Home] Cluster %s: Snapshot report for potential problem %s' % (clusterName, errors[0])
    else:
        msg["Subject"] = '[Call Home] Snapshot report for potential problem %s' % errors[0]

    return msg