import logging
import os, sys, subprocess
from os.path import normpath, expanduser
from os.path import join as joinpath
from os.path import split as splitpath
from subprocess import STDOUT
from pprint import pprint, pformat
from skopt.core.query import Query
from skopt.core.taskdict import gettaskdict
from skopt.core.parameters import update_parameters

def islistofstr(arg, msg=None, dflt=None):
    """Check an argument is a list of strings or a default type.
    Return message + argument's value otherwise.
    """
    if arg is dflt or all([isinstance(item, str) for item in arg]):
        return True
    else:
        if msg is None:
            msg = "Expecting string or list of strings, not:"
        errmsg = pformat(arg)
        return "".join([msg, errmsg])
    

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
        self.outfile = normpath(expanduser(out))
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
    """Wrapper class to update files with new parameter values.

    At least one file is output with iteration number and parameters
    provided at the time of task execution.
    The task initialisation defines where to write the parameters.
    In addition to the default file, template may be provided.
    For exact handling of file names and working directory check the 
    docs of the function assigned to self.func.
    """
    def __init__(self, parfile=None, wd='.', templates=None, *args, **kwargs):
        """Create a task that would write parameters to specified file(s).

        Args:
            parfile (str): File name for the default file with parameters.
            wd      (str): Working directory, where `parfile` file is written.
                The full path to parfile is obtained by joining wd and parfile.
                But the full path to `templates` depends on whether `templates`
                contain a path component in them or not. If they do not, then
                wd is prepended to them; typically, they should have a path.
            templates (str, or list of strings): Template files, containing
                placeholders of Python's old string-formatting style --
                %(Name)Type, which are updated according to the parameters'
                names and values.
            parnames (str or list of string): This is accepted as a kwarg only
                and is meant to supplement the `parameters` argument during
                a call if `parameters` is merely a list of values (no names).
            logger (logging.Logger): kwarg only; Message logger; defaults to
                module logger at DEBUG level.
        """
        self.logger   = kwargs.get('logger', logging.getLogger(__name__))
        # parnames may be None, string, or a list of strings
        self.parnames = kwargs.get('parnames', None)
        if isinstance(self.parnames, str): self.parnames = [self.parnames,]
        assert islistofstr(self.parnames)
        self.func = update_parameters
        # setup parfile path
        (path, name) = splitpath(parfile)
        if path:
            self.parfile = normpath(expanduser(parfile))
        else:
            self.parfile = normpath(expanduser(joinpath(wd, parfile)))
        # templates may be None, string, or a list of strings
        if isinstance(templates, str): templates = [templates, ]
        assert islistofstr(templates)
        if templates:
            for ii, ftempl in enumerate(templates):
                (path, name) = splitpath(ftempl)
                if path:
                    templates[ii] = normpath(expanduser(ftempl))
                else:
                    templates[ii] = normpath(expanduser(joinpath(wd, ftempl)))
        self.templates = templates
        # bunch all in kwargs
        self.args = args
        self.kwargs = kwargs
        # update kwargs with the local modifications
        self.kwargs['parfile'] = self.parfile
        self.kwargs['parnames'] = self.parnames
        self.kwargs['templates'] = self.templates
        self.kwargs['logger'] = self.logger
        self.kwargs['templates'] = self.templates
        # report task initialisation
        self.logger.debug(self.__repr__())

    def __call__(self, parameters, iteration=None):
        """Write the parameters to relevant files.

        Args:
            parameters (list): Parameter values or parameter objects
            iteration (int or tuple of ints): Iteration number; may be
                a tuple, e.g. (generation, individual)
        """
        self.logger.debug("Setting parameters for iteration {} in {}.".
                format(iteration, self.parfile))
        self.func(parameters, iteration, *self.args, **self.kwargs)

    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("{:<15s}: {}".format("SetTask via", pformat(self.func.__name__)))
        s.append("{:<15s}: {}".format("Param. file", pformat(self.parfile)))
        s.append("{:<15s}: {}".format("Templ. files", pformat(self.templates)))
        if self.parnames:
            s.append("{:<15s}: {}".format("Param. names", pformat(self.parnames)))
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
            specification of a callable task.

        exedict (dict): A dictionary of name-aliased user-accessible 
            external executables commands.
        parnames (list): A list of parameter names. Note that typically
            an optimiser has no knowledge of parameter meaning, or names.
            But for various reasons, it is important to have the 
            association between parameter names and parameter values.
            This association is established before setting up the task(s)
            that update model files with the parameter values, and 
            `parnames` is the way to communicate that info to the 
            relevant tasks.

    Returns:
        list: A list of callable task object that can be executed in order.
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
