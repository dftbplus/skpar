import unittest
import logging
import numpy as np
import numpy.testing as nptest
import os
import sys
from os.path import abspath, normpath, expanduser
from skpar.core.input import parse_input
from skpar.core.evaluate import Evaluator, eval_objectives,\
                                cost_rms, create_workdir
from skpar.core.optimise import Optimiser, get_optargs
from skpar.core.database import Database, Query
from skpar.core.tasks import initialise_tasks
from skpar.core import taskdict as core_taskdict
from pprint import pformat, pprint

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

class OptimiseTest(unittest.TestCase):
    """
    Verify basic functionality of optimiser
    """
    def test_parse_input(self):
        """Can we parse input, create an optimiser instance, and run the tasks?
        """
        filename = "skpar_in_optimise.yaml"
        taskdict, tasklist, objectives, optimisation, config =\
            parse_input(filename)
        print (taskdict)
        print (tasklist)
        workroot = config.get('workroot', None)
        templatedir = config.get('templatedir', None)
        create_workdir(workroot, templatedir)
        algo, options, parameters = optimisation
        parnames = [p.name for p in parameters]
        evaluate = Evaluator(objectives, tasklist, taskdict, parnames, config)
        optimiser = Optimiser(algo, parameters, evaluate, options)
        # initialise parameter values, pretending to be optimisation engine
        params = np.array([10.0, -2.5, 0.5, 0.05])
        for pini, par in zip(params, optimiser.parameters):
            par.value = pini
        logger.debug ("### ---------------------------------------- ###")
        logger.debug ("### ----------- Parameters ----------------- ###")
        logger.debug ("### ---------------------------------------- ###")
        for pp in optimiser.parameters:
            logger.debug (pp)

        # initialise tasks manually
        optimiser.evaluate.tasks = initialise_tasks(tasklist, taskdict,
                                                    report=True)
        env = {'workroot': workroot,
               'parameternames': parnames,
               'parametervalues': params,
               'iteration': None}
        workdir = workroot
        database = Database()

        # check task 0
        self.assertEqual(optimiser.evaluate.tasks[0].name, 'set')
        self.assertEqual(optimiser.evaluate.tasks[0].func,
                         core_taskdict.substitute_parameters)
        self.assertEqual(optimiser.evaluate.tasks[0].args,
                         [['template.parameters.dat']])
        optimiser.evaluate.tasks[0](env, database)
        parfile = os.path.abspath(os.path.join(workdir, 'parameters.dat'))
        raw = np.loadtxt(parfile, dtype=[('keys', 'S15'), ('values', 'float')])
        _values = np.array([pair[1] for pair in raw])
        _names = [pair[0].decode("utf-8") for pair in raw]
        nptest.assert_array_equal(params, _values)
        self.assertListEqual(parnames, _names)

        # check task 1
        exe = 'python3'.split()
        self.assertEqual(optimiser.evaluate.tasks[1].name, 'run')
        self.assertEqual(optimiser.evaluate.tasks[1].func,
                         core_taskdict.execute)
        self.assertEqual(optimiser.evaluate.tasks[1].args,
                         ['python3 model_poly3.py'])
        optimiser.evaluate.tasks[1](env, database)

        # check task 2
        self.assertEqual(optimiser.evaluate.tasks[2].name, 'get')
        self.assertEqual(optimiser.evaluate.tasks[2].func,
                         core_taskdict.get_model_data)
        self.assertEqual(optimiser.evaluate.tasks[2].args,
                         ['yval', 'model_poly3_out.dat', 'poly3'])
        optimiser.evaluate.tasks[2](env, database)
        modeldb = database.get('poly3') 
        self.assertTrue(modeldb is not None)
        datafile = os.path.abspath(os.path.join(workdir, 'model_poly3_out.dat'))
        dataout = np.loadtxt(datafile)
        nptest.assert_array_equal(modeldb['yval'], dataout)
        logger.debug("Model DB poly3:")
        logger.debug(database.get('poly3').items())

    def test_optimisation_run(self):
        """Can we parse input, create an optimiser instance, and run the tasks?
        """
        filename   = "skpar_in_optimise.yaml"
        taskdict, tasklist, objectives, optimisation, config =\
                parse_input(filename)
        algo, options, parameters = optimisation
        parnames = [p.name for p in parameters]
        evaluate = Evaluator(objectives, tasklist, taskdict, parnames, config)
        optimiser = Optimiser(algo, parameters, evaluate, options)
        self.assertEqual(len(optimiser.optimise.swarm), 4)
        self.assertEqual(optimiser.optimise.ngen, 8)
        # the pso.toolbox makes evaluate object into a partial function,
        # hence below we have to use the .func to make the correct comparison
        self.assertTrue(optimiser.optimise.toolbox.evaluate.func is evaluate)
        optimiser()
        logger.debug("GBest iteration   : {}".\
                     format(optimiser.optimise.swarm.gbest_iteration))
        logger.debug("GBest fitness     : {}".\
                     format(optimiser.optimise.swarm.gbest.fitness.values))
        gbestpars = optimiser.optimise.swarm.gbest.renormalized
        logger.debug("GBest parameters  : {}".format(gbestpars))
        ideal = np.array([10.0, -2.5, 0.5, 0.05])
        nptest.assert_almost_equal(gbestpars, ideal, decimal=2)


class EvaluateSiTest(unittest.TestCase):
    """
    Verify we can evaluate correctly the fitness for Si from old calculations
    """
    def test_parse_input(self):
        """Can we parse input, create an evaluator instance, and run the tasks?
        """
        filename   = "skpar_in_Si.yaml"
        testfolder = "test_eval_Si"
        # parfile    = os.path.join(testfolder, 'current.par')
        taskdict, tasklist, objectives, optimisation, config =\
                parse_input(filename)
        workroot = config.get('workroot', None)
        templatedir = config.get('templatedir', None)
        create_workdir(workroot, templatedir)
        parnames = None
        evaluate = Evaluator(objectives, tasklist, taskdict, parnames, config)
        if optimisation is None:
            # check evaluation
            cost = evaluate(None, None)
            self.assertTrue(cost < np.atleast_1d(0.23))


if __name__ == '__main__':
    unittest.main()
