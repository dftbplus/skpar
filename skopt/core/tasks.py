import logging
import os, sys, subprocess
from os.path import abspath, normpath, expanduser
from os.path import join as joinpath
from os.path import split as splitpath
import numpy as np
from subprocess import STDOUT
from pprint import pprint, pformat
from skopt.core.query import Query
from skopt.core.taskdict import gettaskdict, plottaskdict
from skopt.core.parameters import update_parameters
from skopt.core.utils import get_logger

module_logger = get_logger('skopt.tasks')

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

def islistoflists(arg):
    """Return True if item is a list of lists.
    """
    tf = False
    if isinstance(arg, list):
        if isinstance(arg[0], list):
            tf = True
    return tf
    

class RunTask (object):
    """
    """
    def __init__(self, cmd, wd='.', inp=None, out='out.log', 
                 err=subprocess.STDOUT, exedict=None, *args, **kwargs):
        #self.logger = kwargs.get('logger', logging.getLogger(__name__))
        self.logger = module_logger
        # handle the path properly!
        self.wd = abspath(expanduser(wd))
        try:
            # should work if cmd is a string
            _cmd = cmd.split()
        except AttributeError:
            # if cmd is a list of strings
            _cmd = cmd
        # separate executable from arguments
        exe  = _cmd[0]
        # args will be empty list if there are no arguments
        args = _cmd[1:]
        # remap the executable; accept even a command with args
        if exedict is not None:
            true_cmd  = exedict.get(exe, exe).split()
            exe = true_cmd[0]
            args = true_cmd[1:] + args
        # We must analyse if there is a path component to the exe,
        # and if so, make it absolute; alternatively, we assume the
        # exe is on the PATH
        if splitpath(exe)[0]:
            exe = abspath(expanduser(exe))
        # make the command into a list, in preparation for subprocess
        self.cmd = exe.split()
        # add the command arguments to the list
        self.cmd.extend(args)
        # deal with input and output files, if any
        if inp is not None:
            try:
                _inp = inp.split()
            except AttributeError:
                _inp = inp
            self.cmd.extend(_inp)
        if out is not None:
            self.outfile = joinpath(self.wd, out)
        else:
            self.outfile = None
        self.err = err

    def __call__(self):
        # Remember top level directory where skopt is invoked
        # We must make every effort to return here even if task
        # fails for some reason!
        topdir = os.getcwd()
        # Go to task working directory
        try:
            os.chdir(self.wd)
        except:
            self.logger.critical("Cannot change to working directory {}".format(self.wd))
            raise
        # Try to execute the task
        try:
            self.logger.debug("Running {} in {}...".format(self.cmd, os.path.relpath(self.wd)))
            # capture the output/error if any, for eventual checks
            self.out = subprocess.check_output(self.cmd, 
                                          universal_newlines=True, 
                                          stderr=subprocess.STDOUT)
            try:
                with open(self.outfile, 'w') as fp:
                    fp.write(self.out)
                self.logger.debug("Done.  : output is in {}.\n".format(os.path.relpath(self.outfile)))
            except TypeError:
                # self.outfile is None
                self.logger.debug("Done.  : outfile was None; output discarded.\n")
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
            self.logger.critical("If the command is a script, make sure there is a shebang!")
            self.logger.critical(self.__repr__())
            self.logger.debug(os.getcwd())
            # go back to top dir
            os.chdir(topdir)
            raise

    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("{:9s}{:<15s}: {}".format("","RunTask in", os.path.relpath(self.wd)))
        s.append("{:9s}{:<15s}: {}".format("","command", pformat(' '.join(self.cmd))))
        s.append("{:9s}{:<15s}: {}".format("","out/err", os.path.relpath(self.outfile)))
        return "\n" + "\n".join(s)


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
        #self.logger   = kwargs.get('logger', logging.getLogger(__name__))
        self.logger = module_logger
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
        # report task initialisation
        # self.logger.debug(self.__repr__())

    def __call__(self, parameters, iteration=None):
        """Write the parameters to relevant files.

        Args:
            parameters (list): Parameter values or parameter objects
            iteration (int or tuple of ints): Iteration number; may be
                a tuple, e.g. (generation, individual)
        """
        self.logger.debug("Setting parameters for iteration {} in {}.".
                format(iteration, os.path.relpath(self.parfile)))
        self.func(parameters, iteration, *self.args, **self.kwargs)

    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("{:9s}{:<15s}: {}".format("", "SetTask via", pformat(self.func.__name__)))
        s.append("{:9s}{:<15s}: {}".format("", "Param. file", os.path.relpath(self.parfile)))
        if self.templates:
            s.append("{:9s}{:<15s}: {}".format("", "Templ. files", 
                " ".join(["{}".format(os.path.relpath(ff)) for ff in self.templates])))
        if self.parnames:
            s.append("{:9s}{:<15s}: {}".format("", "Param. names", pformat(self.parnames)))
        return '\n'+'\n'.join(s)


class GetTask (object):
    """Wrapper class to declare tasks w/ arguments but calls w/o args"""
    def __init__(self, func, source, destination, *args, **kwargs):
        self.func = func
        self.logger = module_logger
        assert isinstance (source, str)
        self.src_name = source
        dbref = Query.get_modeldb(source)
        # see if a database exists
        if dbref is not None:
            self.src = dbref
        else:
            # assume it is a directory or file, and `func` will handle it
            # watch out for the ~/ in the filename!!!
            self.src = normpath(expanduser(source))
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
        s.append("{:9s}{:<15s}: {} ".format("", "GetTask", self.func.__name__))
        s.append("{:9s}{:<15s}: {} ".format("", "func", self.func))
        s.append("{:9s}{:<15s}: {:<15s} {:>10s} {:s}".format("", "from", 
            os.path.relpath(self.src_name), "to :", os.path.relpath(self.dst_name)))
        s.append("{:9s}{:<15s}: {}".format("", "args", pformat(self.args)))
        s.append("{:9s}{:<15s}: {}".format("", "kwargs", pformat(self.kwargs)))
        return '\n'+'\n'.join(s)


class PlotTask (object):
    """Wrapper class to plot model and reference data associated with an objective."""

    def __init__(self, func, plotname, objectives, abscissa_key, **kwargs):
        self.func = func
        self.logger = module_logger
        # How to get the ordinates: from objectives 
        # Notabene: the tasks do not have direct visibility of objectives
        # In fact, objectives may not be declared/initialise at the time 
        # of PlotTask initialisation.
        # Therefore, a higher authority must deal with the assignment.
        # Here we can only record users selection rules.
        #if isinstance(objectives, list): doesn't work if we give only one objective
        if islistoflists(objectives) or isinstance(objectives[0], int):
            self.objv_selectors = objectives
        else:
            self.objv_selectors = [objectives, ]
        # How to get the abscissas: assume a get-task put it in the model DB
        # We can declare queries, but first we need to have reference to
        # the model_names associated with an objective -> again, a higher
        # authority is needed, who must call the self.pick_objectives
        self.abscissa_key = abscissa_key
        self.absc_queries = []
        # Extra queries serve to pass extra data to plotting routine, 
        # e.g. k-labels and ticks etc.
        self.extra_query_keys = kwargs.get('queries', None)
        if self.extra_query_keys and not isinstance(self.extra_query_keys, list):
                self.extra_query_keys = [self.extra_query_keys,]
        # how to make up the plot name
        self.plotname = plotname
        # The following are passed to the back end plotting routine 
        # (e.g. matplotlib) so pass them directly upon call
        self.kwargs = kwargs

    def pick_objectives(self, objectives):
        """Get the references corresponding to the objective tags.
        """
        if isinstance(self.objv_selectors[0], int):
            # Since objectives are declared via a list, indexing is viable
            # option for their selection, but may fail if objectives are
            # updated, while the plot task not, etc.
            # -1 below is to allow Fortran indexing by user, starting from 1
            self.objectives = [objectives[ix-1] for ix in self.objv_selectors]
        else:
            # The more general option assumes [(query_key, model_names), ...]
            # This may capture more than one objectives, but should be OK, since
            # in such a case the type of data will be the same
            assert len(self.objv_selectors[0])==2, self.objv_selectors[0]
            self.objectives = []
            for objv in objectives:
                for item in self.objv_selectors:
                    keys, models = item
                    if objv.query_key == keys and objv.model_names == models:
                        self.objectives.append(objv)
        # Once we have the objectives, we know also their model names
        # and we can create queries for the abscissa key and extra query keys
        if self.abscissa_key is not None:
            for item in self.objectives:
                self.absc_queries.append(Query(item.model_names, self.abscissa_key))
        if self.extra_query_keys is not None:
            self.extra_queries = []
            # extract all models from the list of objectives and create a 
            # list of queries -- one per model
            allmodels = []
            for item in self.objectives:
                if isinstance(item.model_names, str):
                    allmodels.append(item.model_names)
                else:
                    assert isinstance(item.model_names, list)
                    allmodels.extend(item.model_names)
            # this destroys order: allmodels = set(allmodels)
            seen = set()
            osetmodels = [m for m in allmodels if m not in seen and not seen.add(m)]
            for model in osetmodels:
                for qkey in self.extra_query_keys:
                    self.extra_queries.append(Query(model, qkey))

    def __call__(self, iteration):
        """Prepare data for the plot and tag the plot-name with iteration.
        """
        # get xy for plotting
        abscissas  = []
        ordinates  = []
        subweights = []
        for i, item in enumerate(self.objectives):
            # keep the subweights separate
            objvdata = item.get()  # model_data, ref_data, subweights
            # make sure ordinates are first, so as to plot ref below model
            ordinates.append((objvdata[1], objvdata[0])) # ref_data, model_data
            self.logger.debug("Ordinates shape for plotted Objective {}: {}{}".
                    format(i, objvdata[1].shape, objvdata[0].shape))
            subweights.append(objvdata[2])
            # may be we can do this once only and assign self.abscissas...?
            if self.absc_queries:
                self.logger.debug("Querying for abscissas {}:".format(self.absc_queries[i]))
                absc = self.absc_queries[i]()
            else:
                self.logger.debug("Constructing abscissas.")
                if objvdata[1].ndim == 2:
                    absc = np.arange(objvdata[0].shape[1], dtype=int)
                else:
                    # assume 1D array... may break for key-value pairs...
                    absc = np.arange(len(objvdata[0]), dtype=int)
            abscissas.append(absc)
            self.logger.debug("Abscissas shape for plotted Objective {}: {}".
                    format(i, absc.shape))
        # ordinates is now a list of tuples, each tuple being (ref, model)
        # abscissas is now a list of the same size as ordinates
        # items in the lists may be of different type and size, depending on objectives
        # ideally, we may parse and present them according to their type,
        # i.e. kesy-values by markers, others by lines, etc.
        # But in any case, we must map a set of x and y and provide
        # different color for model and for ref.
        self.logger.debug('Collected {} abscissa and {} ordinate sets'.
                format(len(abscissas), len(ordinates)))
        xval = []
        yval = []
        for xx, yy in zip(abscissas, ordinates):
            y1, y2 = yy[0], yy[1] # y1 = list of ref, y2 = list of model data
            yval.append(y1)
            yval.append(y2)
            xval.append(xx)
            xval.append(xx)
        assert len(xval) == len(yval), (len(xval), len(yval))
        #for x, y in zip(xval, yval):
        #    self.logger.debug((x.shape, y.shape))
        #    assert x.shape[0] == y.shape[-1], (x.shape, y.shape)
        self.logger.debug('Overall length of abscissa and ordinate sets: {} {}'.
                format(len(xval), len(yval)))

        # Get data from extra queries
        if self.extra_query_keys is not None:
            # make a dictionary with query.key for keys and lists of data
            # each datum corresponding to a model
            qkeys = set(q.key for q in self.extra_queries)
            extradata = {key: [] for key in qkeys}
            for query in self.extra_queries:
                # Note that in pick_objectives we made a set(allmodels) and 
                # created one query per model, and model_names is a string
                mn = query.model_names
                qk = query.key
                self.logger.debug("Querying {} for {}:".format(mn, qk))
                mdb = query.get_modeldb(mn)
                qdata = query(atleast_1d=False)
                # note that plotting routines will not have knowledge
                # about model names, hence pass on only query key and data
                extradata[qk].append(qdata)
            self.kwargs['extra_data'] = extradata

        # Set colors: draw all objectives with the same color, distinguish 
        # only ref vs model unless explicit user spec is given
        if self.kwargs.get('colors', None) is None:
            colors = []
            for i in range(int(len(yval)/2)):
                # note how yval is composed above: 
                # y1 is ref (blue) y2 is model (red)
                colors.append('b')
                colors.append('r')
            self.kwargs['colors'] = colors

        # tag the plot-name by iteration
        if iteration is not None:
            try:
                # should work if iteration is a tuple
                plotname = "{:s}_{:d}-{:d}".format(self.plotname, *iteration)
                title    = "{:s} ({:d}-{:d})".format(os.path.split(self.plotname)[-1], *iteration)
            except TypeError:
                # if iteration is a single integer, rather than a sequence
                plotname = "{:s}_{:d}".format(self.plotname, iteration)
                title    = "{:s} ({:d})".format(os.path.split(self.plotname)[-1], *iteration)
        else:
            plotname = self.plotname
            title    = os.path.split(self.plotname)[-1]
        self.kwargs['title'] = title
        # set legend labels (only 2 labels by default, consistent with 
        # the colour setting
        self.kwargs['ylabels'] = ['ref', 'model']
        # try to plot
        # ignore subweights for the moment
        self.func(plotname, xval, yval, **self.kwargs)
        
    def __repr__(self):
        """Yield a summary of the task.
        """
        s = []
        s.append("{:9s}{:<15s}: {} ".format("", "PlotTask", self.func.__name__))
        s.append("{:9s}{:<15s}: {} ".format("", "func", self.func))
        s.append("{:9s}{:<15s}: {} ".format("", "plot-name", self.plotname))
        s.append("{:9s}{:<15s}: {} ".format("", "abscissas", self.abscissa_key))
        try:
            s.append("{:9s}{:<15s}: {} ".format("", "ordinates", 
                '\n         '.join(["{}: {}".format(item.query_key, item.model_names) 
                    for item in self.objectives])))
        except AttributeError:
            s.append("{:9s}{:<15s}: {} ".format("", "objectives", 
                '\n{:9s}'.join(["{}".format(item) for item in self.objv_selectors])))
        s.append("{:9s}{:<15s}: {}".format("", "kwargs", pformat(self.kwargs)))
        return '\n'+'\n'.join(s)


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
    #
    tasklist = []
    logger = module_logger
    # the spec list has definitions of different tasks
    for item in spec:
        (tasktype, taskargs), = item.items()
        if 'set' == tasktype.lower():
            try: 
                tasklist.append(SetTask(*taskargs, parnames=parnames))
            except TypeError:
                # end up here if unknown task type, which is mapped to None
                logger.debug ('Cannot handle the following task specification:')
                logger.debug (spec)
                raise
        if 'run' == tasktype.lower():
            try: 
                tasklist.append(RunTask(*taskargs, exedict=exedict))
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
        if 'plot' == tasktype.lower():
            assert len(taskargs) >= 3,\
                "A plot task must have at least 3 arguments:"\
                "PlotFunction, Plotname, Objectives, Optional Abscissa-Key, Optional kwargs"
            # 1. Assign the real function to 1st arg
            func = plottaskdict[taskargs[0]]
            taskargs[0] = func
            # 2. Check if we have optional dictionary of arguments
            if isinstance(taskargs[-1], dict):
                optkwargs = taskargs[-1]
                optkwargs.update(kwargs)
                del taskargs[-1]
            else:
                optkwargs = kwargs
            # 3. Check if we have an abscissa key or not
            if len(taskargs) == 3:
                taskargs.append(None)
            # 4. Register the task in the task-list
            try:
                tasklist.append(PlotTask(*taskargs, **optkwargs))
            except TypeError:
                # end up here if unknown task type, which is mapped to None
                logger.debug ('Cannot handle the following task specification:')
                logger.debug (spec)
                raise
    return tasklist
