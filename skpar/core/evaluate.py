"""Evaluator engine of SKPAR."""
import os
import shutil
import numpy as np
from skpar.core.utils import get_logger, normalise
from skpar.core.tasks import initialise_tasks
from skpar.core.database import Database

LOGGER = get_logger(__name__)

DEFAULT_GLOBAL_COST_FUNC = "rms"

DEFAULT_CONFIG = {
    'workroot': None,
    'templatedir': None,
    'keepworkdirs': True,
}


def abserr(ref, model):
    """Return the per-element difference model and reference.
    """
    aref = np.asarray(ref)
    amod = np.asarray(model)
    assert aref.shape == amod.shape, (aref.shape, amod.shape)
    return amod - aref

def relerr(ref, model):
    """Return the per-element relative difference between model and reference.

    To handle cases where `ref` vanish, and possibly `model` vanish
    at the same time, we:

        * translate directly a vanishing absolute error into vanishing
          relative error (where both `ref` and `model` vanish.

        * take the model as a denominator, thus yielding 1, where
          `ref` vanishes but `model` is non zero
    """
    aref = np.asarray(ref)
    amod = np.asarray(model)
    # get deviations
    err = abserr(aref, amod)
    # fix the denominator
    denom = aref.copy()
    denom[aref == 0.] = amod[aref == 0.]
    # assert 0 absolute error even for 0 denominator
    rel_err = np.zeros(err.shape)
    rel_err[err != 0] = err[err != 0] / denom[err != 0]
    return rel_err

def cost_rms(ref, model, weights, errf=abserr):
    """Return the weighted-RMS deviation"""
    assert np.asarray(ref).shape == np.asarray(model).shape
    assert np.asarray(ref).shape == np.asarray(weights).shape
    err2 = errf(ref, model) ** 2
    rms = np.sqrt(np.sum(weights*err2))
    return rms

def eval_objectives(objectives, database):
    """Evaluate fitness/cost"""
    fitness = np.array([objv(database) for objv in objectives])
    return fitness

# ----------------------------------------------------------------------
# Function mappers
# ----------------------------------------------------------------------
# use small letters for the function names; make sure
# the input parser coerces any capitalisation in advance

# cost functions
COSTF = {"rms": cost_rms, }

# error types
ERRF = {"abs": abserr, "rel": relerr, "abserr": abserr, "relerr": relerr,}
# ----------------------------------------------------------------------


class Evaluator():
    """**Evaluator**

    The evaluator is the only thing visible to the optimiser.
    It has several things to do:

    1. Accept a list of parameter values (or key-value pairs),
       and an iteration number (or a tuple: (e.g. generation,particle_index)).

    2. Update tasks (and underlying models) with new parameter values.

    3. Execute the tasks to obtain model data with the new parameters.

    4. Evaluate fitness for individual objectives.

    5. Evaluate global fitness (cost) and return the value. It may be
       good to also return the max error, to be used as a stopping criterion.

    """
    def __init__(self, objectives, tasklist, taskdict, parameternames,
                 config=None, costf=COSTF[DEFAULT_GLOBAL_COST_FUNC],
                 utopia=None, verbose=False):
        self.objectives = objectives
        self.weights = normalise([oo.weight for oo in objectives])
        self.tasklist = tasklist # list of name,options pairs
        self.taskdict = taskdict # name:function mapping
        self.parnames = parameternames
        self.config = config if config is not None else DEFAULT_CONFIG
        self.costf = costf
        if utopia is None:
            self.utopia = np.zeros(len(objectives))
        else:
            assert len(utopia) == len(objectives), (len(utopia), len(objectives))
            self.utopia = utopia
        # configure logger
        self.logger = LOGGER
        if verbose:
            self._msg = self.logger.info
        else:
            self._msg = self.logger.debug
        # report objectives; these do not change over time
        for item in objectives:
            self._msg(item)

    def evaluate(self, parametervalues, iteration=None):
        """Evaluate the global fitness of a given point in parameter space.

        This is the only object accessible to the optimiser, therefore only
        two arguments can be passed.

        Args:
            parametervalues (list): current point in design/parameter space
            iteration: (int or tupple): current iteration or current
                generation and individual index within generation

        Return:
            fitness (float): global fitness of the current design point
        """

        # Create individual working directory for each evaluation
        origdir = os.getcwd()
        workroot = self.config['workroot']
        if workroot is None:
            workdir = origdir
        else:
            workdir = get_workdir(iteration, workroot)
            create_workdir(workdir, self.config['templatedir'])

        # Initialise model database
        self.logger.info('Initialising ModelDataBase.')
        # database may be something different than a dictionary, but
        # whatever object it is, should have:
        #     update_modeldb(modelname, datadict) -- update modeldb
        #     get_modeldb(modelname) -- return a ref to modeldb
        # The point is that for every individual evaluation, we must
        # have individual model DB, so evaluations can be done in parallel.
        database = Database()
        # database = {} currently works too
        # Wrap the environment in a single dict
        env = {'workroot': workdir,
               'logger': self.logger,
               'parameternames': self.parnames,
               'parametervalues': parametervalues,
               'iteration': iteration,
               'taskdict': self.taskdict,
               'objectives': self.objectives
              }
        # Initialise and then execute the tasks
        tasks = initialise_tasks(self.tasklist, self.taskdict, report=False)
        self.logger.info('Iteration %s', iteration)
        self.logger.info('===========================')
        if self.parnames:
            parstr = ['{:s}({:.4g})'.format(name, val) for
                      name, val in zip(self.parnames, parametervalues)]
            self.logger.info('Parameters: {:s}'.format(' '.join(parstr)))
#        do we really need to pass workdir and to os.chdir???
#        move the for loop to a function.
#        execute_tasks(tasks, env, database, workdir, logger)
        for i, task in enumerate(tasks):
            os.chdir(workdir)
            try:
                task(env, database)
            except:
                self.logger.critical('Task %i FAILED:\n%s', i, task)
                raise

        # Evaluate individual fitness for each objective
        objvfitness = eval_objectives(self.objectives, database)
        # Evaluate global fitness
        cost = self.costf(self.utopia, objvfitness, self.weights)
        self._msg('{:<15s}: {}\n'.format('Overall cost', cost))

        # Remove iteration-specific working dir if not needed:
        if (not self.config['keepworkdirs']) and (workroot is not None):
            destroy_workdir(workdir)
        os.chdir(origdir)

        return np.atleast_1d(cost)

    def __call__(self, parametervalues, iteration=None):
        return self.evaluate(parametervalues, iteration)

    def __repr__(self):
        srepr = []
        srepr.append('Evaluator:')
        srepr.append('\n-- Tasks:')
        srepr.append('--------------------')
#        for item in self.tasks:
#            srepr.append(item.__repr__())
        srepr.append('\n-- Objectives:')
        srepr.append('--------------------')
        for item in self.objectives:
            srepr.append(item.__repr__())
        srepr.append('\n-- Cost Func.:')
        srepr.append('--------------------')
        srepr.append(self.costf.__name__)
        return '\n'.join(srepr)


def get_workdir(iteration, workroot):
    """Find what is the root of the work-tree at a given iteration"""
    if workroot is None:
        workdir = None
    else:
        if iteration is None:
            myworkdir = 'noiter'
        else:
            try:
                myworkdir = '-'.join([str(it) for it in iteration])
            except TypeError:
                myworkdir = str(iteration)
        workdir = os.path.abspath(os.path.join(workroot, myworkdir))
    return workdir


def create_workdir(workdir, templatedir):
    """Create a new and clean work directory tree from template"""
    if workdir is None:
        return
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    if templatedir is not None:
        shutil.copytree(templatedir, workdir, symlinks=True)
    else:
        os.mkdir(workdir)


def destroy_workdir(workdir):
    """Remove the entire work directory tree"""
    if workdir is not None:
        shutil.rmtree(workdir)
