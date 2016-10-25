import logging
import os, sys, subprocess
from subprocess import STDOUT


class RunTask (object):
    
    def __init__(self, exe, wd='.', inp=None, out='out.log', err=STDOUT, logger=None):
        self.wd = wd
        if isinstance(exe, list):
            self.cmd = exe
        else:
            self.cmd = [exe,]
        if isinstance(inp, list):
            self.cmd.extend(inp)
        else:
            if inp is not None:
                self.cmd.append(inp)
        self.outfile = out
        self.err = err
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

    def __call__(self):
        # Remember top level directory where skopt is invoked
        # We must make every effort to return here even if task
        # fails for some reason!
        topdir = os.getcwd()
        # Go to taks working directory
        os.chdir(os.path.abspath(self.wd))
        # Try to execute the task
        try:
            self.logger.debug("Running {0} in {1}...".format(self.cmd,self.wd))
            # capture the output/error if any, for eventual checks
            self.out = subprocess.check_output(self.cmd, 
                                          universal_newlines=True, 
                                          stderr=self.err)
            with open(self.outfile, 'w') as fp:
                fp.write(self.out)
            self.logger.debug("Complete: output is in {0}".format(self.out))
            # return to caller's directory
            os.chdir(topdir)
        except subprocess.CalledProcessError as exc:
            # report the issue and exit
            self.logger.critical('{} failed with exit status {}\n'.
                            format(self.cmd, exc.returncode))
            self.out = exc.output
            with open(self.outfile, 'w') as fp:
                fp.write(self.out)
            # go back to top dir
            os.chdir(topdir)
            raise
