import unittest
import logging
import numpy as np
import numpy.testing as nptest
import os
from os.path import normpath, expanduser
from skopt.input import parse_input
from skopt.evaluate import Evaluator, eval_objectives, cost_RMS
from skopt.optimise import Optimiser, get_optargs
from skopt.query import Query

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

class OptimiseTest(unittest.TestCase):
    """
    Verify basic functionality of optimiser
    """
    def test_parse_input(self):
        """Can we parse input, create an optimiser instance, and run the tasks?"""
        Query.flush_modelsdb()
        filename   = "test_optimise.yaml"
        testfolder = "test_optimise"
        parfile    = os.path.join(testfolder, 'current.par')
        tasks, objectives, optimisation = parse_input(filename)
        algo, options, parameters = optimisation
        evaluate = Evaluator(objectives, tasks)
        optimiser = Optimiser(algo, parameters, evaluate, **options)
        logger.debug ("\n### -------------------------------------------------- ###")
        logger.debug ("### ----------- Tasks -------------------------------- ###")
        logger.debug ("### -------------------------------------------------- ###")
        for tt in optimiser.evaluate.tasks:
            logger.debug (tt)
        logger.debug ("\n### -------------------------------------------------- ###")
        logger.debug ("### ----------- Objectives --------------------------- ###")
        logger.debug ("### -------------------------------------------------- ###")
        for oo in optimiser.evaluate.objectives:
            logger.debug (oo)
        # initialise parameter values, pretending to be optimisation engine
        params = np.array([10.0, -2.5, 0.5, 0.05])
        for pini, par in zip(params, optimiser.parameters):
            par.value = pini
        logger.debug ("\n### -------------------------------------------------- ###")
        logger.debug ("### ----------- Parameters --------------------------- ###")
        logger.debug ("### -------------------------------------------------- ###")
        for pp in optimiser.parameters:
            logger.debug (pp)
        try:
            os.remove(parfile)
            os.remove('model_poly3_out.dat')
        except:
            pass
        # check task 0 (SetTask)
        names  = ['c0', 'c1', 'c2', 'c3']
        optimiser.evaluate.tasks[0](optimiser.parameters)
        raw = np.loadtxt(parfile, dtype=[('keys', 'S15'), ('values', 'float')])
        _params = np.array([pair[1] for pair in raw])
        _names = [pair[0].decode("utf-8") for pair in raw]
        nptest.assert_array_equal(params, _params)
        self.assertListEqual(names, _names)
        # check task 1 (RunTask)
        exe = normpath(expanduser('~/anaconda3/python'))
        self.assertListEqual(optimiser.evaluate.tasks[1].cmd, [exe, 'model_poly3.py'])
        self.assertEqual(optimiser.evaluate.tasks[1].wd, 'test_optimise')
        optimiser.evaluate.tasks[1]()
        # check task 2 (GetTask)
        optimiser.evaluate.tasks[2]()
        modeldb = Query.get_modeldb('poly3') 
        self.assertTrue(modeldb is not None)
        dataout = np.loadtxt('test_optimise/model_poly3_out.dat')
        nptest.assert_array_equal(modeldb['yval'], dataout)
        logger.debug("Model DB poly3:")
        logger.debug(Query.get_modeldb('poly3').items())
        # check evaluation
        objvfitness = eval_objectives(evaluate.objectives)
        nptest.assert_almost_equal(objvfitness, np.zeros(len(objectives)))
        logger.debug("Individual objective fitness: {}".format(objvfitness))
        logger.debug(evaluate.costf.__name__)
        logger.debug(evaluate.costf)
        fitness = evaluate.costf(evaluate.utopia, objvfitness, evaluate.weights)
        logger.debug("Global fitness: {}".format(fitness))
        nptest.assert_almost_equal(fitness, np.atleast_1d(0))
        

    def test_optimisation_run(self):
        """Can we parse input, create an optimiser instance, and run the tasks?"""
        Query.flush_modelsdb()
        filename   = "test_optimise.yaml"
        testfolder = "test_optimise"
        parfile    = os.path.join(testfolder, 'current.par')
        tasks, objectives, optimisation = parse_input(filename)
        algo, options, parameters = optimisation
        evaluate   = Evaluator(objectives, tasks)
        optimiser  = Optimiser(algo, parameters, evaluate, **options)
        self.assertEqual(len(optimiser.optimise.swarm), 4)
        self.assertEqual(optimiser.optimise.ngen, 5)
        # the pso.toolbox makes evaluate object into a partial function,
        # hence below we have to use the .func to make the correct comparison
        self.assertTrue(optimiser.optimise.toolbox.evaluate.func is evaluate)
        try:
            os.remove(parfile)
            os.remove('model_poly3_out.dat')
        except:
            pass
        optimiser()
        logger.debug("GBest iteration   : {}".format(optimiser.optimise.swarm.gbest_iteration))
        logger.debug("GBest fitness     : {}".format(optimiser.optimise.swarm.gbest.fitness.values))
        gbestpars = optimiser.optimise.swarm.gbest.renormalized
        logger.debug("GBest parameters  : {}".format(gbestpars))
        ideal = np.array([10.0, -2.5, 0.5, 0.05])
        nptest.assert_almost_equal(gbestpars, ideal, decimal=2)


class EvaluateSiTest(unittest.TestCase):
    """
    Verify we can evaluate correctly the fitness for Si from old calculations
    """
    def test_parse_input(self):
        """Can we parse input, create an evaluator instance, and run the tasks?"""
        Query.flush_modelsdb()
        filename   = "skopt_in_Si.yaml"
        testfolder = "test_eval_Si"
        parfile    = os.path.join(testfolder, 'current.par')
        tasks, objectives, optimisation = parse_input(filename)
        evaluate = Evaluator(objectives, tasks)
        logger.debug('Evaluation only:')
        if optimisation is None:
            logger.debug ("\n### -------------------------------------------------- ###")
            logger.debug ("### ----------- Tasks -------------------------------- ###")
            logger.debug ("### -------------------------------------------------- ###")
            for tt in evaluate.tasks:
                logger.debug (tt)
            logger.debug ("\n### -------------------------------------------------- ###")
            logger.debug ("### ----------- Objectives --------------------------- ###")
            logger.debug ("### -------------------------------------------------- ###")
            for oo in evaluate.objectives:
                logger.debug (oo)
            for tt in evaluate.tasks:
                tt()
                # check evaluation
            objvfitness = eval_objectives(evaluate.objectives)
            #nptest.assert_almost_equal(objvfitness, np.zeros(len(objectives)))
            logger.debug("Individual objective fitness: {}".format(objvfitness))
            logger.debug(evaluate.costf.__name__)
            logger.debug(evaluate.costf)
            fitness = evaluate.costf(evaluate.utopia, objvfitness, evaluate.weights)
            logger.debug("Global fitness: {}".format(fitness))
            self.assertTrue(fitness < np.atleast_1d(0.2))
        

if __name__ == '__main__':
    unittest.main()
