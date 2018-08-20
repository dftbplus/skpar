"""Tasks module, defining relevant classes and functions"""
import os
import sys
from pprint import pformat, pprint
import numpy as np
from skpar.core.query import Query
from skpar.core.utils import get_logger

LOGGER = get_logger(__name__)

def get_tasklist(userinp):
    """Return a list of tuples of task names and task arguments."""
    if userinp is None:
        LOGGER.critical('Missing "tasks:" in user input; Nothing to do. Bye!')
        sys.exit(1)
    tasklist = []
    for item in userinp:
        # due to json/yaml specifics, a task is represented as a dictionary with
        # one item only, hence the comma after task, avoiding looping over items
        (taskname, taskargs), = item.items()
        task = (taskname, taskargs)
        tasklist.append(task)
    return tasklist

def check_taskdict(tasklist, taskdict):
    """Check task names are in the task dictionary; quit otherwise."""
    for task in tasklist:
        if task[0] not in taskdict.keys():
            LOGGER.critical('Task {:s} not in TASKDIR; Cannot continue'.\
                            format(task[0]))
            LOGGER.critical('Check spelling and verify import of user modules')
            sys.exit(1)

def initialise_tasks(tasklist, taskdict, report=False):
    """Transform a tasklist into a list of callables as per taskdict.

    Args:
        tasklist(list): a list of (task-name, user-arguments) pairs
        taskdict(dict): a dictionary mapping task names to actual functions

    Returns:
        tasks(list): callable objects, instances of Task class
    """
    LOGGER.info('Initialising tasks')
    tasks = []
    for taskname, argslist in tasklist:
        func = taskdict[taskname]
        assert isinstance(argslist, (list, tuple)),\
            ("Make sure task arguments are within []; IsString?: {}".\
             format(isinstance(argslist, str)))
        tasks.append(Task(taskname, func, argslist))

    if report:
        LOGGER.info("The following tasks will be executed at each iteration.")
        for i, task in enumerate(tasks):
            LOGGER.info("Task {:d}:\t{:s}".format(i, task.__repr__()))
    return tasks


class Task(object):
    """Generic wrapper over functions or executables.
    """
    def __init__(self, name, func, fargs):
        """Create a callable object from user input"""
        self.name = name
        self.func = func
        self.fargs = fargs
    #
    def __call__(self, env, database):
        """Execute the task, let caller handle any exception raised by func"""
        self.func(env, database, *self.fargs)
    #
    def __repr__(self):
        """Yield a summary of the task.
        """
        srepr = []
        srepr.append('{:s} ({})'.format(self.name, self.func))
        srepr.append('\t{:d} args: {:s}'.format(len(self.fargs),
            ', '.join(['{}'.format(arg) for arg in self.fargs])))
        return "\n".join(srepr)


class PlotTask (object):
    """Plot to file the model and reference data associated with one or more objectives.
    
    Note that model and reference data constitute the Y-coordinates (ordinates).
    The X-coordinates (abscissas) are potentially held in a separate field of
    the model data dictionary, and implicitly it is assumed that the X-coordinates
    of the reference data are the same (else the model-vs-reference comparison
    would make no sense).
    The fundamental concept is that we want to visualise our objectives.
    So the ordinate can be obtained by the user's stating which objectives is
    to be visualised.
    The challenge is that a definition of objective contains no info about the
    abscissa, so it has to be explicitly specified by the user or else the
    default indexing of the reference or model data items will be used as
    abscissa.
    The whole mechanism must work with the simplest possible (default)
    plotting routine, as well as with a more specialised plotter object.
    The initialisation of the PlotTask should establish what dictionary
    items are to be plotted as abscissas and ordinates and from which
    model dictionary, and how the latter are matched to the corresponding
    reference data. Recall however, that objectives may not be visible
    at the time the task is initialised. So at init time, we merely 
    record the user's directions. Later – at call time – we do the data
    queries and call the plot function with the latest model data.
    """
    def __init__(self, func, plotname, objectives, abscissa_key, **kwargs):
        """Establish which dictionary items make for abscissas and ordinates.
        """
        self.func = func
        self.logger = LOGGER
        # How to get the ordinates: from objectives
        # Notabene: the tasks do not have direct visibility of objectives
        # In fact, objectives may not be declared/initialised at the time
        # of PlotTask initialisation.
        # Therefore, a higher authority must deal with the assignment.
        # Here we can only record user's selection rules.
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
        # for the decoration of the x and y axes, e.g. k-ticks and 
        # k-labels for a bandstructure plot, etc.
        self.extra_query_keys = kwargs.get('queries', None)
        if self.extra_query_keys and not isinstance(self.extra_query_keys, list):
                self.extra_query_keys = [self.extra_query_keys,]
        # how to make up the plot name
        self.plotname = plotname
        # The following are passed to the back end plotting routine
        # (e.g. matplotlib) so pass them directly upon call
        self.kwargs = kwargs
        # clean up the kwargs that has been processed here
        try:
            del self.kwargs['queries']
        except KeyError:
            pass

    def pick_objectives(self, objectives):
        """Get the references corresponding to the objective tags.

        This function acquired the reference data that must be plotted,
        by analysing the objectives referred to in the definition of
        the plot task. It is not called within the init of the plot task
        itself, since at the time the plot task is being declared,
        the objectives may not yet be. So a separate agency is suppoosed
        to call this method once both objectives and task are declared.
        Currently this happens within input.py -- at the end of processing
        of the input file.
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
        
        At the time of call, the model data has been updated and can be
        obtained by querying the model data dictionary.
        Also, iteration number, possibly fitness and parameter values can
        be passed to the backend plotting routine
        """
        # get xy for plotting
        abscissas  = []
        ordinates  = []
        subweights = []
        for i, item in enumerate(self.objectives):
            # keep the subweights separate
            objvdata = item.get()  # returns model_data, ref_data, subweights
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
                self.kwargs[qk] = qdata

        # Set colors: draw all objectives with the same color, distinguish
        # only ref vs model unless explicit user spec is given
        if self.kwargs.get('colors', None) is None:
            colors = []
            for i in range(int(len(yval)/2.)):
                # note how yval is composed above:
                # y1 is ref (blue) y2 is model (orange)
                colors.append('#1f77b4')
                colors.append('#ff7f0e') 
            self.kwargs['colors'] = colors

        # tag the plot-name by iteration number; embed it in the plot title
        if iteration is not None:
            try:
                # should work if iteration is a tuple
                plotname = '{:s}_{:s}'.format(self.plotname, '-'.join([str(it) for it in iteration]))
                title    = '{:s} ({:s})'.format(os.path.split(self.plotname)[-1],
                        '_'.join([str(it) for it in iteration]))
            except TypeError:
                # if iteration is a single integer, rather than a sequence
                plotname = "{:s}_{:d}".format(self.plotname, iteration)
                title    = "{:s} ({:d})".format(os.path.split(self.plotname)[-1], iteration)
        else:
            plotname = self.plotname
            title    = os.path.split(self.plotname)[-1]
        self.kwargs['title'] = title
        # set legend labels (only 2 labels by default, consistent with
        # the colour setting
        self.kwargs['linelabels'] = ['ref', 'model']
        # Try to plot
        # Ignore subweights for the moment, although these may decorate later,
        # e.g. width of the model bands.
        # The following self.kwargs are passed:
        # title, linelabels, colors, extra queries and extra incoming kwargs.
        # The extra incoming kwargs may contain plot specific stuff, like 
        # x/ylimits, etc.
        self.func(xval, yval, filename=plotname+'.pdf', **self.kwargs)

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


def set_tasks(spec, exedict=None, parnames=None):
    """Parse user specification of Tasks, and return a list of Tasks for execution.

    Args:
        spec (list): List of dictionaries, each dictionary being a,
            specification of a callable task.
        exedict (dict): A dictionary of name-aliased user-accessible external
            executables commands.
        parnames (list): A list of parameter names. Note that typically an
            optimiser has no knowledge of parameter meaning, or names.  But for
            various reasons, it is important to have the association between
            parameter names and parameter values.  This association is
            established before setting up the task(s) that update model files
            with the parameter values, and `parnames` is the way to communicate
            that info to the relevant tasks.

    Returns:
        list: A list of callable task object that can be executed in order.

    """
    #
    if spec is None:
        LOGGER.error('Missing "tasks:" in user input: nothing to do. Bye!')
        sys.exit(1)

    tasklist = []
    LOGGER = LOGGER
    # the spec list has definitions of different tasks
    for item in spec:
        (tasktype, taskargs), = item.items()
        if 'set' == tasktype.lower():
            try:
                tasklist.append(SetTask(parnames=parnames, *taskargs))
            except TypeError:
                LOGGER.debug('Cannot handle the following task specification:')
                LOGGER.debug(spec)
                raise

        if 'run' == tasktype.lower():
            try:
                tasklist.append(RunTask(*taskargs, exedict=exedict))
            except TypeError:
                LOGGER.debug ('Cannot handle the following task specification:')
                LOGGER.debug(spec)
                raise

        if 'get' == tasktype.lower():
            assert isinstance(taskargs, list)
            # 1. Assign the real function to 1st arg
            func = GETTASKDICT[taskargs[0]]
            taskargs[0] = func
            # 2. Check if we have optional dictionary of arguments
            if isinstance(taskargs[-1], dict):
                optkwargs = taskargs[-1]
                del taskargs[-1]
            else:
                optkwargs = {}
            #BA: Would be weird when source was a directory and not a key!
            # 3. Check if we have a missing destination and assign the source
            if len(taskargs) == 2:
                taskargs.append(taskargs[1])
            # 4. Register the task in the task-list
            try:
                tasklist.append(GetTask(*taskargs, **optkwargs))
            except TypeError:
                LOGGER.debug ('Cannot handle the following task specification:')
                LOGGER.debug (spec)
                raise

        if 'plot' == tasktype.lower():
            assert len(taskargs) >= 3,\
                "A plot task must have at least 3 arguments:"\
                "PlotFunction, Plotname, Objectives, Optional Abscissa-Key, Optional kwargs"
            # 1. Assign the real function to 1st arg
            func = PLOTTASKDICT[taskargs[0]]
            taskargs[0] = func
            # 2. Check if we have optional dictionary of arguments
            if isinstance(taskargs[-1], dict):
                optkwargs = taskargs[-1]
                del taskargs[-1]
            else:
                optkwargs = {}
            # 3. Check if we have an abscissa key or not
            if len(taskargs) == 3:
                taskargs.append(None)
            # 4. Register the task in the task-list
            try:
                tasklist.append(PlotTask(*taskargs, **optkwargs))
            except TypeError:
                # end up here if unknown task type, which is mapped to None
                LOGGER.debug ('Cannot handle the following task specification:')
                LOGGER.debug (spec)
                raise
    return tasklist
