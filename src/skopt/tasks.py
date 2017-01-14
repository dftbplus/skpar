import logging
import os, sys, subprocess
from os.path import normpath, expanduser
from subprocess import STDOUT
from pprint import pprint, pformat
from skopt.query import Query
from skopt.taskdict import gettaskdict

DEFAULT_PARAMETER_FILE='current.par'


class RunTask (object):
    """
    """
    
    def __init__(self, cmd, wd='.', inp=None, out='out.log', 
            err=subprocess.STDOUT, exedict=None, *args, **kwargs):
        self.logger = kwargs.get('logger', logging.getLogger(__name__))
        self.wd = wd
        try:
            _cmd = cmd.split()
        except AttributeError:
            # if cmd is a list of strings
            _cmd = cmd
        exe  = _cmd[0]
        # args will be empty list if there are no arguments
        args = _cmd[1:]
        # remap the executable; accept even a command with args
        if exedict is not None:
            self.cmd = exedict.get(exe, exe)
            self.cmd = normpath(expanduser(self.cmd))
            self.cmd = self.cmd.split()
        else:
            self.cmd = exe.split()
        self.cmd.extend(args)
        if inp is not None:
            try:
                _inp = inp.split()
            except AttributeError:
                _inp = inp
            self.cmd.extend(_inp)
        self.outfile = out
        self.err = err

    def __call__(self):
        # Remember top level directory where skopt is invoked
        # We must make every effort to return here even if task
        # fails for some reason!
        topdir = os.getcwd()
        # Go to task working directory
        try:
            os.chdir(os.path.abspath(self.wd))
        except:
            self.logger.critical("Cannot change to working directory {}".format(self.wd))
            raise
        # Try to execute the task
        try:
            self.logger.debug("Running {} in {}...".format(self.cmd, self.wd))
            # capture the output/error if any, for eventual checks
            self.out = subprocess.check_output(self.cmd, 
                                          universal_newlines=True, 
                                          stderr=subprocess.STDOUT)
            with open(self.outfile, 'w') as fp:
                fp.write(self.out)
            self.logger.debug("Complete: output is in {}".format(self.outfile))
            # return to caller's directory
            os.chdir(topdir)
        except subprocess.CalledProcessError as exc:
            # report the issue and exit
            self.logger.critical('The following task failed with exit status {}:\n'.
                            format(exc.returncode))
            self.logger.critical(self.__repr__())
            self.out = exc.output
            with open(self.outfile, 'w') as fp:
                fp.write(self.out)
            # go back to top dir
            os.chdir(topdir)
            raise
        except OSError:
            self.logger.critical("Abnormal termination -- the OS could not handle the command of:")
            self.logger.critical(self.__repr__())
            # go back to top dir
            os.chdir(topdir)
            raise

    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("{:<15s}: {}".format("RunTask in", pformat(self.wd)))
        s.append("{:<15s}: {}".format("command", pformat(' '.join(self.cmd))))
        s.append("{:<15s}: {}".format("out/err", pformat(self.outfile)))
        s.append("\n")
        return "\n".join(s)


class SetTask (object):
    """
    """
    def __init__(self, parfile=DEFAULT_PARAMETER_FILE, wd='.', 
            append=False, parnames=None, *args, **kwargs):
        self.parfile = parfile
        self.wd = wd
        assert not append, ("Append mode not supported yet by SetTask")
        self.logger = kwargs.get('logger', logging.getLogger(__name__))
        self.parnames = parnames

    def __call__(self, parameters, iteration=None):
        self.logger.debug("Setting parameteres for iteration {} in {}.".
                format(iteration, self.parfile))
        parfile = os.path.join(self.wd, self.parfile)
        parout = []
        if self.parnames is not None:
            assert len(parameters) == len(self.parnames)
            for name, par in zip(self.parnames, parameters):
                try:
                    parout.append("{:>20s}  {}".format(name, par.value))
                except AttributeError:
                    parout.append("{:>20s}  {}".format(name, par))
        else:
            for par in parameters:
                try:
                    parout.append("{:>20s}  {}".format(par.name, par.value))
                except AttributeError:
                    parout.append(str(par))
            
        with open(parfile, 'w') as fp:
            if iteration is not None:
                fp.writelines('#{}\n'.format(iteration))
            fp.writelines('\n'.join(parout))

    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("{:<15s}: {}".format("SetTask in", pformat(self.wd)))
        s.append("{:<15s}: {}".format("param. file", pformat(self.parfile)))
        s.append("\n")
        return "\n".join(s)


class GetTask (object):
    """Wrapper class to declare tasks w/ arguments but calls w/o args"""
    def __init__(self, func, source, destination, *args, **kwargs):
        self.func = func
        self.logger = kwargs.get('logger', logging.getLogger(__name__))
        assert isinstance (source, str)
        self.src_name = source
        dbref = Query.get_modeldb(source)
        # see if a database exists
        if dbref is not None:
            self.src = dbref
        else:
            # assume it is a directory or file, and `func` will handle it
            self.src = source
        self.dst_name = destination
        self.dst  = Query.add_modelsdb(destination)
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        try:
            self.func(self.src, self.dst, *self.args, **self.kwargs)
        except:
            self.logger.critical("FAILED attempt to call {} with the following args:\n{} and kwargs:\n{}".
                    format(self.func.__name__, self.args, self.kwargs))
            raise
        
    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("{:<10s}: {} ".format("GetTask", self.func.__name__))
        s.append("{:<10s}: {} ".format("func", self.func))
        s.append("{:<10s}: {:<15s} {:<10s} {:<15s}".format("from", 
            self.src_name, "to", self.dst_name))
        s.append("{:<10s}: {}".format("args", pformat(self.args)))
        s.append("{:<10s}: {}".format("kwargs", pformat(self.kwargs)))
        s.append("\n")
        return "\n".join(s)


def set_tasks(spec, exedict=None, parnames=None, *args, **kwargs):
    """Parse user specification of Tasks, and return a list of Tasks for execution.

    Args:
        spec (list): List of dictionaries, each dictionary being a,
            specification of a task of a recognised type.

    Returns:
        list: a List of instances of task classes, each 
            corresponding to a recognised task type.
    """
    logger = kwargs.get('logger', logging.getLogger(__name__))
    kwargs['logger'] = logger
    #
    tasklist = []
    # the spec list has definitions of different tasks
    for item in spec:
        (tasktype, taskargs), = item.items()
        if 'set' == tasktype.lower():
            try: 
                tasklist.append(SetTask(*taskargs, parnames=parnames, logger=logger))
            except TypeError:
                # end up here if unknown task type, which is mapped to None
                logger.debug ('Cannot handle the following task specification:')
                logger.debug (spec)
                raise
        if 'run' == tasktype.lower():
            try: 
                tasklist.append(RunTask(*taskargs, exedict=exedict, logger=logger))
            except TypeError:
                # end up here if unknown task type, which is mapped to None
                logger.debug ('Cannot handle the following task specification:')
                logger.debug (spec)
                raise
        if 'get' == tasktype.lower():
            assert isinstance(taskargs, list)
            # 1. Assign the real function to 1st arg
            func = gettaskdict[taskargs[0]]
            taskargs[0] = func
            # 2. Check if we have optional dictionary of arguments
            if isinstance(taskargs[-1], dict):
                optkwargs = taskargs[-1]
                optkwargs.update(kwargs)
                del taskargs[-1]
            else:
                optkwargs = kwargs
            # 3. Check if we have a missing destination and assign the source
            if len(taskargs) == 2:
                taskargs.append(taskargs[1])
            # 4. Register the task in the task-list
            try: 
                tasklist.append(GetTask(*taskargs, **optkwargs))
            except TypeError:
                # end up here if unknown task type, which is mapped to None
                logger.debug ('Cannot handle the following task specification:')
                logger.debug (spec)
                raise
    return tasklist
