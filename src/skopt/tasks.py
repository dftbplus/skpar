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
            err=subprocess.STDOUT, exedict=None, logger=None):
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger
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
            append=False, parnames=None, logger=None):
        self.parfile = parfile
        self.wd = wd
        assert not append, ("Append mode not supported yet by SetTask")
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger
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
        kwargs = self.kwargs
        if not kwargs:
            self.func(self.src, self.dst, *self.args)
        else:
            try:
                self.func(self.src, self.dst, *self.args, **kwargs)
            except:
                logger.critical("FAILED attempt to call {} with the following kwargs".
                        format(self.func.__name__, kwargs))
        
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


taskmapper = {'run': RunTask, 'set': SetTask, 'get': GetTask}

# def get_task(spec, logger=None, **kwargs):
#     """Return an instance of a task, as defined in the input spec.
# 
#    Args:
#        spec (dict): a dictionary with a single entry, being
#            tasktype: {dict with the arguments of the task}
#
#    Returns:
#        list: an instance of the corresponding task-types class.
#    """
#    (ttype, args), = spec.items()
#    try:
#        #a0 = args.pop(0)
#        #task = taskmapper[ttype](a0, *args, **kwargs)
#        task = taskmapper[ttype](*args, **kwargs)
#    except TypeError:
#        # end up here if unknown task type, which is mapped to None
#        print ('Cannot handle the following task specification:')
#        print (spec)
#        raise
#    return task

def set_tasks(spec, exedict=None, parnames=None, logger=None):
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
        (tasktype, args), = item.items()
        if tasktype.lower() == 'set':
            try: 
                tasklist.append(SetTask(*args, parnames=parnames, logger=logger))
            except TypeError:
                # end up here if unknown task type, which is mapped to None
                logger.debug ('Cannot handle the following task specification:')
                logger.debug (spec)
                raise
        if tasktype.lower() == 'run':
            try: 
                tasklist.append(RunTask(*args, exedict=exedict, logger=logger))
            except TypeError:
                # end up here if unknown task type, which is mapped to None
                logger.debug ('Cannot handle the following task specification:')
                logger.debug (spec)
                raise
        if tasktype.lower() == 'get':
            if isinstance(args[0], str):
                func = gettaskdict[args[0]]
                args[0] = func
            try: 
                tasklist.append(GetTask(*args, logger=logger))
            except TypeError:
                # end up here if unknown task type, which is mapped to None
                logger.debug ('Cannot handle the following task specification:')
                logger.debug (spec)
                raise
    return tasklist
