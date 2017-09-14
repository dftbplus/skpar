"""
"""
import os
import shutil
import logging
import numpy as np
from skpar.core.utils import get_logger, normalise
from skpar.core.tasks import SetTask, PlotTask

module_logger = get_logger('skpar.evaluate')

DEFAULT_GLOBAL_COST_FUNC = "rms"

DEFAULT_CONFIG = {
    'workroot': None,
    'templatedir': None,
    'keepworkdirs': True,
}


def abserr(ref, model):
    """Return the per-element difference model and reference.
    """
    rr = np.asarray(ref)
    mm = np.asarray(model)
    assert rr.shape == mm.shape, (rr.shape, mm.shape)
    return mm - ref

def relerr(ref, model):
    """Return the per-element relative difference between model and reference.

    To handle cases where `ref` vanish, and possibly `model` vanish
    at the same time, we:

        * translate directly a vanishing absolute error into vanishing
          relative error (where both `ref` and `model` vanish.

        * take the model as a denominator, thus yielding 1, where
          `ref` vanishes but `model` is non zero
    """
    rr = np.asarray(ref)
    mm = np.asarray(model)
    # get deviations
    err = abserr(rr, mm)
    # fix the denominator
    denom = rr.copy()
    denom[rr == 0.] = mm[rr == 0.]
    # assert 0 absolute error even for 0 denominator
    rele = np.zeros(err.shape)
    rele[err != 0] = err[err != 0] / denom[err != 0]
    return rele

def cost_RMS(ref, model, weights, errf=abserr):
    """Return the weighted-RMS deviation"""
    assert np.asarray(ref).shape == np.asarray(model).shape
    assert np.asarray(ref).shape == np.asarray(weights).shape
    err2 = errf(ref, model) ** 2
    rms = np.sqrt(np.sum(weights*err2))
    return rms

def eval_objectives(objectives):
    """
    """
    fitness = np.array([objv() for objv in objectives])
    return fitness

# ----------------------------------------------------------------------
# Function mappers
# ----------------------------------------------------------------------
# use small letters for the function names; make sure
# the input parser coerces any capitalisation in advance

# cost functions
costf = {"rms": cost_RMS, }

# error types
errf = {"abs": abserr, "rel": relerr, "abserr": abserr, "relerr": relerr,}
# ----------------------------------------------------------------------


class Evaluator (object):
    """**Evaluator**

    The evaluator is the only thing visible to the optimiser.
    It has several things to do:

    1. Accept a list (or dict?) of parameter values (or key-value pairs),
       and an iteration number (or a tuple: (generation,particle_index)).

    2. Update tasks (and underlying models) with new parameter values.

    3. Execute the tasks to obtain model data with the new parameters.

    4. Evaluate fitness for individual objectives.

    5. Evaluate global fitness (cost) and return the value. It may be
       good to also return the max error, to be used as a stopping criterion.

    """
    def __init__(self, objectives, tasks, config=None,
                 costf=costf[DEFAULT_GLOBAL_COST_FUNC], utopia=None,
                 verbose=False, **kwargs):
        self.objectives = objectives
        self.weights = normalise([oo.weight for oo in objectives])
        self.tasks = tasks
        self.config = config if config is not None else DEFAULT_CONFIG
        workroot = self.config['workroot']
        if workroot is not None:
            workroot = os.path.abspath(workroot)
            if not os.path.exists(workroot):
                os.makedirs(workroot)
        self.costf = costf
        if utopia is None:
            self.utopia = np.zeros(len(self.objectives))
        else:
            assert len(utopia) == len(objectives), (len(utopia), len(objectives))
            self.utopia = utopia
        self.verbose = verbose
        self.logger = module_logger
        # report all tasks and objectives
        if self.verbose:
            self.msg = self.logger.info
        else:
            self.msg = self.logger.debug
        for item in tasks:
            self.msg(item)
        for item in objectives:
            self.msg(item)

    def evaluate(self, parameters, iteration=None):
        """Evaluate the global fitness of a given point in parameter space.

        This is the only object accessible to the optimiser.

        Args:
            parameters (list or dict): current point in design/parameter space
            iteration: (int or tupple): current iteration or current
                generation and individual index within generation

        Return:
            fitness (float): global fitness of the current design point
        """

        # Create particles individual working directory
        origdir = os.getcwd()
        workroot = self.config['workroot']
        if workroot is None:
            workdir = origdir
        else:
            workdir = get_workdir(iteration, workroot)
            create_workdir(workdir, self.config['templatedir'])

        # Update models with new parameters.
        # Updating the models should be the first task in the tasks list,
        # but user may decide to omit it in some situations (e.g. if only
        # interested in evaluating the set of models, not optimising).
        jj = 0
        task = self.tasks[jj]
        if isinstance(task, SetTask):
            if parameters is None:
                self.logger.warning('Omitting task 1 due to None parameters:')
                self.logger.debug(task)
            else:
                self.msg('Iteration : {}'.format(iteration))
                self.msg('Parameters: {:s}'.format(", ".join(["{:.6f}".format(p) for p in parameters])))
                os.chdir(workdir)
                task(workdir, parameters, iteration)
            jj = 1
        # Get new model data by executing the rest of the tasks
        for ii, task in enumerate(self.tasks[jj:]):
            kk = ii + jj
            os.chdir(workdir)
            try:
                if isinstance(task, PlotTask):
                    task(iteration)
                else:
                    task(workdir)
            except:
                self.logger.critical('Evaluation FAILED at task {}:\n{}'.format(kk+1, task))
                raise

        # Evaluate individual fitness for each objective
        self.objvfitness = eval_objectives(self.objectives)
        ref = self.utopia
        # evaluate global fitness
        cost = self.costf(ref, self.objvfitness, self.weights)
        self.msg('{:<15s}: {}\n'.format('Overall cost', cost))

        # Remove particle specific working dir if not needed:
        if (not self.config['keepworkdirs']) and (workroot is not None):
            destroy_workdir(workdir)
        os.chdir(origdir)

        return np.atleast_1d(cost)

    def __call__(self, parameters, iteration=None):
        return self.evaluate(parameters, iteration)

    def __repr__(self):
        ss = []
        ss.append('Evaluator:')
        ss.append('\n-- Tasks:')
        ss.append('--------------------')
        for item in self.tasks:
            ss.append(item.__repr__())
        ss.append('\n-- Objectives:')
        ss.append('--------------------')
        for item in self.objectives:
            ss.append(item.__repr__())
        ss.append('\n-- Cost Func.:')
        ss.append('--------------------')
        ss.append(self.costf.__name__)
        return '\n'.join(ss)


def get_workdir(iteration, workroot):
    if workroot is None:
        workdir = None
    else:
        if iteration is None:
            myworkdir = 'noiter'
        else:
            myworkdir = '-'.join([str(it) for it in iteration])
        workdir = os.path.abspath(os.path.join(workroot, myworkdir))
    return workdir


def create_workdir(workdir, templatedir):
    if workdir is None:
        return
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    if templatedir is not None:
        shutil.copytree(templatedir, workdir, symlinks=True)
    else:
        os.mkdir(workdir)


def destroy_workdir(workdir):
    if workdir is not None:
        shutil.rmtree(workdir)
