import logging
import os, sys, subprocess
from subprocess import STDOUT
from pprint import pprint, pformat
from skopt.query import Query
from skopt.taskdict import taskdict

DEFAULT_PARAMETER_FILE='current.par'
parameterfile = DEFAULT_PARAMETER_FILE

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
        # Go to task working directory
        os.chdir(os.path.abspath(self.wd))
        # Try to execute the task
        try:
            self.logger.debug("Running {} in {}...".format(self.cmd, self.wd))
            # capture the output/error if any, for eventual checks
            self.out = subprocess.check_output(self.cmd, 
                                          universal_newlines=True, 
                                          stderr=self.err)
            with open(self.outfile, 'w') as fp:
                fp.write(self.out)
            self.logger.debug("Complete: output is in {}".format(self.out))
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

    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("\n")
        s.append("{:<15s}: {}".format("RunTask in", pformat(self.wd)))
        s.append("{:<15s}: {}".format("command", pformat(' '.join(self.cmd))))
        s.append("{:<15s}: {}".format("out/err", pformat(self.outfile)))
        return "\n".join(s)


class SetTask (object):
    
    def __init__(self, parfile=DEFAULT_PARAMETER_FILE, wd='.', append=False):
        self.parfile = parfile
        self.wd = wd

    def __call__(self, parameters, iteration):
        self.logger.debug("\nSetting parameteres for iteration {} in {}.".
                format(iteration, self.parfile))
        parfile = os.path.join(self.wd, self.parfile)
        with open(parfile, 'w') as fp:
            fp.writeline('{}\n'.format(iteration))
            fp.writeline('{}\n'.format(parameters))

    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("\n")
        s.append("{:<15s}: {}".format("SetTask in", pformat(self.wd)))
        s.append("{:<15s}: {}".format("param. file", pformat(self.parfile)))
        return "\n".join(s)


class GetTask (object):
    """Wrapper class to declare tasks w/ arguments but calls w/o args"""

    def __init__(self, func, source, destination, *args, **kwargs):
        if isinstance(func, str):
            self.func = taskdict[func]
        else:
            self.func   = func
        # lets make it possible to handle both strings and dictionaries 
        # as source/dest.
        self.src_name = source
        self.src = Query.add_modelsdb(source)
        self.dst_name = destination
        self.dst = Query.add_modelsdb(destination)
        self.args   = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        for arg in args:
            self.args.append(arg)
        self.kwargs.update(**kwargs)
        self.func(self.src, self.dst, *self.args, **self.kwargs)
        
    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("\n")
        s.append("{:<10s}: {} ".format("GetTask", self.func.__name__))
        s.append("{:<10s}: {:<15s} {:<10s} {:<15s}".format("from", 
            self.src_name, "to", self.dst_name))
        s.append("{:<10s}: {}".format("args", pformat(self.args)))
        s.append("{:<10s}: {}".format("kwargs", pformat(self.kwargs)))
        return "\n".join(s)


taskmapper = {'run': RunTask, 'set': SetTask, 'get': GetTask}

def get_task(spec, logger=None):
    """Return an instance of a task, as defined in the input spec.

    Args:
        spec (dict): a dictionary with a single entry, being
            tasktype: {dict with the arguments of the task}

    Returns:
        list: an instance of the corresponding task-types class.
    """
    (_t, _args), = spec.items()
    try:
        a0 = _args.pop(0)
        a1 = _args.pop(0)
        task = taskmapper[_t](a0, a1, *_args)
    except TypeError:
        # end up here if unknown task type, which is mapped to None
        print ('Cannot handle the following task specification:')
        print (spec)
        raise
    return task

def set_tasks(spec, logger=None):
    """Parse user specification of Tasks, and return a list of Tasks for execution.

    Args:
        spec (list): List of dictionaries, each dictionary being a,
            specification of a task of a recognised type.

    Returns:
        list: a List of instances of task classes, each 
            corresponding to a recognised task type.
    """
    tasklist = []
    # the spec list has definitions of different tasks
    for item in spec:
        tasklist.append(get_task(item))
        print(tasklist[-1])
    return tasklist
