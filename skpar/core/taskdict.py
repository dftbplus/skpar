"""Dictionary with default tasks and their underlying functions."""
import os
import subprocess
import shlex
import shutil
import glob
import numpy as np
from skpar.core.utils import get_ranges, get_logger, islistoflists
from skpar.core.plot import skparplot
from skpar.core.parameters import update_parameters
from skpar.core.database import Query

LOGGER = get_logger(__name__)

def parse_cmd(cmd):
    """Parse shell command for globbing and environment variables.
    """
    if not isinstance(cmd, list):
        cmd = shlex.split(cmd)
    parsed_cmd = [cmd[0],]
    for word in cmd[1:]:
        if word[0] == '$':
            var = word[1:].strip('{').strip('}')
            varval = os.environ.get(var, word)
            parsed_cmd.append(varval)
        else:
            if '*' in word:
                items = glob.glob(word)
                for item in items:
                    parsed_cmd.append(item)
            else:
                parsed_cmd.append(word)
    return parsed_cmd

def execute(implargs, database, cmd, workdir='.', outfile='run.log',
            purge_workdir=False, **kwargs):
    """Execute external command in workdir, streaming output/error to outfile.

    Args:
        implargs (dict): caller environment variables
        database (dict-like): not used, but needed to maintain a task-signature
        cmd (str): command; executed in `implargs['workroot']+workir`;
                   if it contains `$` or `*`-globbing, these are shell-expanded
        workdir (path-like): execution directory relative to workroot
        outfile (str): output file for the stdout/stderr stream; continuously
                       updated during execution
        purge_workdir (bool): if true, any existing working directory is purged
        kwargs (dict): passed directly to the underlying `subprocess.call()`

    Returns:
        None

    Raises:
        OSError: if `cmd` cannot be executed
        RuntimeError: if `cmd` returncode is nonzero
        SubprocessError: other possible circumstances
    """
    # prepare workdir
    origdir = os.getcwd()
    workroot = implargs.get('workroot', '.')
    _workdir = os.path.abspath(os.path.join(workroot, workdir))
    try:
        os.makedirs(_workdir)
    except OSError:
        # directory exists
        if purge_workdir:
            # that's a bit brutal, but saves to worry of links and subdirs
            shutil.rmtree(_workdir)
            os.makedirs(_workdir)
    os.chdir(_workdir)
    # prepare out/err handling
    filename = kwargs.pop('stdout', outfile)
    if filename:
        kwargs['stdout'] = open(filename, 'w')
    filename = kwargs.pop('stderr', None)
    if filename:
        kwargs['stderr'] = open(filename, 'w')
    else:
        kwargs['stderr'] = subprocess.STDOUT
    # execute the command, make sure output is not streamed
    _cmd = parse_cmd(cmd)
    try:
        returncode = subprocess.call(_cmd, **kwargs)
        if returncode:
            LOGGER.critical('Execution of %s FAILED with exit status %d',
                            _cmd, returncode)
            raise RuntimeError
    #
    except subprocess.SubprocessError:
        LOGGER.critical('Subprocess call of {:s} FAILED'.format(_cmd))
        raise
    #
    except (OSError, FileNotFoundError) as exc:
        LOGGER.critical("Abnormal termination: OS could not execute %s in %s",
                        _cmd, _workdir)
        LOGGER.critical("If the command is a script ,"\
                        "check permissions and that is has a shebang!")
        raise
    #
    finally:
        # make sure we return to where we started from in any case!
        os.chdir(origdir)

def get_model_data(implargs, database, item, source, model,
                   rm_columns=None, rm_rows=None, scale=1., **kwargs):
    """Get data from file and put it in a database under a given key.

    Use numpy.loadtxt to get the data from `source` file and write the data
    to `database` under `dst`.`key` field. If `dst` does not exist, it is
    created. All `kwargs` are directly passed to numpy.loadtxt. Additionally,
    some post-processing can be done (removing rows or columns and scaling).

    Args:
        implargs(dict): dictionary of implicit arguments from caller
        database(object): must support dictionary-like get/update()
        source(str): file name source of data; path relative to implargs[workroot]
        model(str): model name to be updated in `database`
        key(str): key under which to store the data in under `dst`
        rm_columns: [ index, index, [ilow, ihigh], otherindex, [otherrange]]
        rm_rows   : [ index, index, [ilow, ihigh], otherindex, [otherrange]]
        scale(float): multiplier of the data
    """
    logger = implargs.get('logger', LOGGER)
    workroot = implargs.get('workroot', '.')
    assert isinstance(source, str), \
        "source must be a filename string, but is {} instead.".\
        format(type(source))
    assert isinstance(item, str),\
        "item must be a string naming the data, but is {} instead."\
            .format(type(item))
    # read file
    fname = os.path.abspath(os.path.join(workroot, source))
    try:
        data = np.loadtxt(fname, **kwargs)
    except ValueError:
        logger.critical('np.loadtxt cannot understand the contents of %s'+\
            'with the given arguments: %s', fname, **kwargs)
        raise
    except (IOError, FileNotFoundError):
        logger.critical('np.loadtxt cannot open %s', fname)
        raise
    # do some filtering on columns and/or rows if requested
    # note that file to 2D-array mapping depends on 'unpack' from
    # kwargs, which transposes the loaded array.
    postprocess = {'rm_columns': rm_columns, 'rm_rows': rm_rows}
    if any(postprocess.values()):
        if kwargs.get('unpack', False):
            # since 'unpack' transposes the array, now row index
            # in the original file is along axis 1, while column index
            # in the original file is along axis 0.
            key1, key2 = ['rm_columns', 'rm_rows']
        else:
            key1, key2 = ['rm_rows', 'rm_columns']
        for axis, key in enumerate([key1, key2]):
            rm_rngs = postprocess.get(key, [])
            if rm_rngs:
                indexes = []
                # flatten, combine and sort, then delete corresp. object
                for rng in get_ranges(rm_rngs):
                    indexes.extend(list(range(*rng)))
                indexes = list(set(indexes))
                indexes.sort()
                data = np.delete(data, obj=indexes, axis=axis)
    data = data * scale
    #
    try:
        # assume model in database
        database.get(model).update({item: data})
    except (KeyError, AttributeError):
        # model not in database
        database.update({model: {item: data}})


def substitute_parameters(implargs, database, templatefiles, **kwargs):
    """Substitute parameters (within implicit arguments) in given templates.
    """
    logger = implargs.get('logger', LOGGER)
    workroot = implargs.get('workroot', '.')
    iteration = implargs.get('iteration', None)
    try:
        parvalues = implargs['parametervalues']
    except KeyError:
        logger.critical('No parameter values found in implicit arguments. '\
                        'Cannot proceed with parameter substitution.')
        raise
    try:
        parnames = implargs['parameternames']
    except KeyError:
        logger.critical('No parameter names found in implicit arguments. '\
                        'Cannot proceed with parameter substitution.')
        raise
    assert (len(parvalues) == len(parnames)), (len(parvalues), len(parnames))
    logger.debug("Substituting parameters for iteration %s in %s.",\
                    iteration, workroot)
    update_parameters(workroot, templatefiles, parvalues, parnames)


def prepare_for_plotsave(iteration, filename):
    """Ensure directory of filename exists and embed iteration number"""
    # Tag filename by iteration
    if iteration is not None:
        try:
            # assume iteration is a tuple
            filename = '{:s}_{:s}'.format(filename,\
                                            '-'.join([str(it) for it \
                                                    in iteration]))
        except TypeError:
            # iteration is a single integer, rather than a tuple
            filename = "{:s}_{:d}".format(filename, iteration)
    # Ensure we have a proper extension
    if os.path.basename(filename).split('.')[-1] not in ['pdf', 'png']:
        filename = filename + '.pdf'
    # Ensure directory where plot is to be saved exists.
    # Note that os.path.dirname may return '', hence the use of abspath.
    # Also, exist_ok = True is a must since if we try to remove/re-create the
    # directory, it may happen to destroy the current directory!
    if not os.path.exists(os.path.abspath(os.path.dirname(filename))):
        os.makedirs(os.path.abspath(os.path.dirname(filename)),
                    exist_ok=True)
    return filename


class PlotTask(object):
    """Wrapper for skparplot; extracts data from objectives prior to plotting.

    This is a callable object that plots to file the model and reference data
    associated with one or more objectives.
    The model and reference data constitute the Y-coordinates (ordinates).
    The X-coordinates (abscissas) are potentially held in a separate field of
    the model data dictionary, and implicitly it is assumed that the
    X-coordinates of the reference data are the same
    (else the model-vs-reference comparison would make no sense).
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
    reference data.
    Note however, that objectives may not be visible at the time the task is
    initialised. So at init time, we merely record the user's directions.
    Later – at call time – we do the data queries and call the plot function
    with the latest model data.
    """
    def __init__(self, func, plotname, objectives, abscissa_key=None, **kwargs):
        """Establish which dictionary items make for abscissas and ordinates.
        """
        # func is a string; global taskdict may be passed via env to
        # resolve it at call time
        self.func = func
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

    def pick_objectives(self, objectives, database):
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
            assert len(self.objv_selectors[0]) == 2, self.objv_selectors[0]
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
                self.absc_queries.append(Query(item.model_names,
                                               self.abscissa_key, database))
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
                    self.extra_queries.append(Query(model, qkey, database))

    def __call__(self, implargs, database):
        """Prepare data for the plot and tag the plot-name with iteration.

        At the time of call, the model data has been updated and can be
        obtained by querying the model data dictionary.
        Also, iteration number, possibly fitness and parameter values can
        be passed to the backend plotting routine
        """
        # parse implargs first
        logger = implargs.get('logger', LOGGER)
        iteration = implargs.get('iteration', None)
        objectives = implargs.get('objectives', None)
        logger.debug('Implicit arguments passed to PlotTask\n%s', implargs)
        self.pick_objectives(objectives, database)
        self.func = implargs.get('taskdict', {}).get(self.func, skparplot)
        logger.debug('Using plotting function %s', self.func)
        # get xy for plotting
        abscissas  = []
        ordinates  = []
        subweights = []
        for i, item in enumerate(self.objectives):
            # keep the subweights separate
            objvdata = item.get(database)  # returns model_data, ref_data, subweights
            # make sure ordinates are first, so as to plot ref below model
            ordinates.append((objvdata[1], objvdata[0])) # ref_data, model_data
            logger.debug("Ordinates shape for plotted Objective {}: {}{}".
                         format(i, objvdata[1].shape, objvdata[0].shape))
            subweights.append(objvdata[2])
            # may be we can do this once only and assign self.abscissas...?
            if self.absc_queries:
                logger.debug("Querying for abscissas {}:".
                             format(self.absc_queries[i]))
                absc = self.absc_queries[i](database)
            else:
                logger.debug("Constructing abscissas.")
                if objvdata[1].ndim == 2:
                    absc = np.arange(objvdata[0].shape[1], dtype=int)
                else:
                    # assume 1D array... may break for key-value pairs...
                    absc = np.arange(len(objvdata[0]), dtype=int)
            abscissas.append(absc)
            logger.debug("Abscissas shape for plotted Objective {}: {}".\
                         format(i, absc.shape))
        # Ordinates is now a list of tuples, each tuple being (ref, model)
        # Abscissas is now a list of the same size as ordinates
        # Items in the lists may be of different type and size, depending on
        # objectives.
        # Ideally, we may parse and present them according to their type,
        # i.e. key-values by markers, others by lines, etc.
        # But in any case, we must map a set of x and y and provide
        # different colour for model and for ref.
        logger.debug('Collected {} abscissa and {} ordinate sets'.\
                     format(len(abscissas), len(ordinates)))
        assert len(ordinates) and len(abscissas),\
                '\nMake sure model names in plot arguments are correct!\n'\
                'Missing data: abscissas: {}; ordinates: {}'.\
                format(len(abscissas), len(ordinates))
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
        #    logger.debug((x.shape, y.shape))
        #    assert x.shape[0] == y.shape[-1], (x.shape, y.shape)
        logger.debug('Overall length of abscissa and ordinate sets: {} {}'.
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
                logger.debug("Querying {} for {}:".format(mn, qk))
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

        # Tag the plot-name by iteration number; embed it in the plot title
        # and prepare directory where plot is to be saved
        filename = prepare_for_plotsave(iteration, self.plotname)
        self.kwargs['title'] = os.path.splitext(os.path.basename(filename))[0]
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
        self.func(xval, yval, filename=filename, **self.kwargs)


def wrapper_PlotTask(env, database, *args, **kwargs):
    """Wrapper around the legacy PlotTask"""
    plot = PlotTask(*args, **kwargs)
    plot(env, database)


TASKDICT = {
    'set': substitute_parameters,
    'sub': substitute_parameters,
    'substitute': substitute_parameters,
    #
    'run': execute,
    'exe': execute,
    'execute': execute,
    #
    'get': get_model_data,
    'get_data': get_model_data,
    #
    'plot': wrapper_PlotTask,
    'plot_objectives': wrapper_PlotTask,
    }
