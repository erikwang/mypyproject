##### data collect class #############################################
##    Data_Collect(path, __name__)  			    ##
##      path - data directory top  where data is to sav		    ##
##      caller_module_name - the module name that invokes the class ## 
######################################################################
import os
import subprocess
import errno
import shutil
import util
from threading import Timer
import signal


class Data_Collect(object):

    def __init__(self, path, moduleName):
        self.savepath = os.path.join(path, moduleName.split('.')[-1])
        self.snplogger = util.getLogger(moduleName + '.' + os.path.splitext(os.path.basename(__file__))[0])

    def makepath(self, path=None):
        if not path:
            self.path = self.savepath
        else:
            self.path = os.path.join(self.savepath, path)
        try:
            os.makedirs(self.path)
        except OSError as exception:
            if exception.errno == errno.EEXIST:
                return True
            else:
                self.snplogger.critical("Failed with error code %s")

                return False

    def runit(self, cmdpath, time_out=15):
        def kill_proc(p):
            p.kill()

        timer = None
        try:
            cmd_proc = subprocess.Popen(cmdpath, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            timer = Timer(time_out, kill_proc, [cmd_proc])
            timer.start()
            self.cmd_out, self.cmd_err = cmd_proc.communicate()

            if cmd_proc.returncode == -signal.SIGKILL:
                self.snplogger.error("%s timeout.", cmdpath)
                return False
            if cmd_proc.returncode != 0:
                if not self.cmd_out:
                    raise RuntimeError("%s failed, status code %s stdout %s stderr %r." %
                                       (cmdpath, cmd_proc.returncode, self.cmd_out, self.cmd_err))
                else:
                    self.snplogger.warning("%s may have failed. status code %s stderr %s.", cmdpath,
                                           cmd_proc.returncode, self.cmd_err)
        except OSError as ose:
            if ose.errno == 2:
                self.snplogger.warning('%s not found.', cmdpath)
                return None
        except Exception as be:
            self.snplogger.warning("%s failed: %s", os.path.basename(cmdpath), str(be))
            return None
        finally:
            if timer:
                timer.cancel()

        return self.cmd_out

    def saveit(self, cmd, cmdpath=None, time_out=15):
        if not cmd:
            self.snplogger.error("Command to run is empty.")
            return False
        if cmdpath:
            cmd = os.path.join(cmdpath, cmd)
        if not self.makepath():
            self.snplogger.debug("%s is not available.", self.savepath)

        self.snplogger.debug('Running %s ...', cmd)
        self.cmd_out = self.runit(cmd, time_out)
        if not self.cmd_out:
            return False
        outputf = open(os.path.join(self.savepath, os.path.basename(cmd).replace(' ', '_')), 'a')
        outputf.write(self.cmd_out)
        outputf.close()
        return True

    def copyit(self, srcPath, desPath=''):
        if not os.path.exists(srcPath):
            self.snplogger.error("Invalid path or file name. '%s'", srcPath)
            return False
        if not desPath:
            desPath = os.path.join(self.savepath, os.path.basename(srcPath))
            self.makepath(self.savepath)
        else:
            desPath = os.path.join(self.savepath, desPath, os.path.basename(srcPath))
            self.makepath(desPath)

        try:
            shutil.copytree(srcPath, desPath)
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                try:
                    shutil.copy2(srcPath, desPath)
                except Exception as e:
                    self.snplogger.error("Copy '%s' to '%s' failed., error: %s", srcPath, desPath, e)
                    return False
            else:
                self.snplogger.error("Copy '%s' failed. Error: %s", srcPath, e)
                return False
        except shutil.Error as exc:
            errors = exc.args[0]
            for error in errors:
                src, dst, msg = error
                try:
                    shutil.copy2(src, dst)
                except:
                    self.snplogger.error("Copy '%s' to '%s' failed. Error: %s", src, dst, msg)
        return True

    def moveit(self, srcPath, desPath=''):
        if not os.path.exists(srcPath):
            self.snplogger.error("Invalid path or file name. '%s'", srcPath)
            return False
        if not desPath:
            desPath = os.path.join(self.savepath, os.path.basename(srcPath))
            self.makepath(self.savepath)
        else:
            desPath = os.path.join(self.savepath, desPath, os.path.basename(srcPath))
            self.makepath(desPath)

        try:
            shutil.move(srcPath, desPath)
        except OSError as e:
            self.snplogger.error("Move '%s' failed. Error: %s", srcPath, e)
            return False
        return True
