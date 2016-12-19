import unittest
import numpy as np
import numpy.testing as nptest
from numpy.polynomial.polynomial import polyval
import logging
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams.update({'font.size': 20, 'font.family': 'sans'})
import os, sys
from deap import base
from skopt.pso import PSO
from skopt.pso import PSO, report_stats

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

class PSOTest(unittest.TestCase):
    """
    A small test and usage example of the PSO engine.
    """
    def test_pso(self):
        """Can we instantiate a PSO and run it?"""
        # Refdata:  5 points from a 3-rd order polynomial
        xmin,xmax = -10, 10
        nref = 5
        xref = np.linspace(xmin+1, xmax-1, nref)
        c = np.array([10, -2.5, 0.5, 0.05])
        refdata = polyval(xref, c)
        logger.debug ("Reference data: {}".format(refdata))
        refweights = np.ones(len(refdata))
        def model (par):
            return polyval(xref, par)

        # Define an evaluator function for the fitness e.g. RMS error.
        # NOTABENE:
        # 1. Fitness must be a tuple-like, hence the atleast_1d below.
        # 2. The PSO requires errors to be returned, to allow for an 
        #    alternative stopping critera. This may become optional.
        # 3. If the evaluate functions supports 'iteration' argument the PSO 
        #    will call it with iteration (generation, particle_index) in the 
        #    argument list.
        # 4. Assumed is that refdata and weights are known in advance; the
        #    PSO does not need to know about them.
        def evaluate(parameters, iteration, refdata=refdata, weights=refweights):
            modeldata = model(parameters)
            errors  = refdata - modeldata
            # it seems at least for this example relative error reduces the
            # no-average-required number of iterations by significantly -
            # e.g. from ~150 to ~ 110, to reduce the ErrTol
            fitness = np.atleast_1d(np.sqrt(sum(weights*np.power(errors/refdata, 2))))         
            #return fitness, np.max(np.abs(errors/refdata))
            return fitness

        # Variables specific to the optimisation problem
        # ----------------------------------------------------------------------
        # Dimensionality and range of the fitting parameters that are representted as a particle:
        # in this case, 4 polynomial coefficients are to be fitted, and we provide appropriate 
        # range for them
        prange = [(-20,20), (-5,5), (-2,2), (-1,1)]
        # Setup the PSO for single objective (one-tuple) minimisation (negative sign)
        # The engine is capable of handling multiple objectives, but this may be
        # explored at a later stage. Here we have scalarised everything in advance.
        objectives = (-1, )
        # number of particles composing the swarm
        npart = 8
        # max number of generations through which the swarm evolves
        ngen = 200
        # max tolerable percentage error (% deviation b/w a target and 
        # evaluated value), used as a stopping criterium
        ErrTol = 0.001   
        # make an instance of the pso
        #pso = PSO(prange, evaluate, objectives=objectives, npart=npart)
        pso = PSO(prange, evaluate, npart=npart, objective_weights=objectives,
                ngen = ngen, ErrTol=ErrTol)

        # buzz the particle swarm for ngen generations or until percentage 
        # deviations are no greater than ErrTol
        swarm, stats = pso()

        logger.debug ("gbest iteration: {0}".format(swarm.gbest_iteration))
        # logger.debug ("gbest fitness: {:.5f}, and worstErr {:.3f} %".
        #    format(swarm.gbest.fitness.values[0], swarm.gbest.worstErr*100.))
        logger.debug ("gbest fitness: {:.5f}".format(swarm.gbest.fitness.values[0]))
        logger.debug ("Fitted coefficients: {}".
            format(", ".join(["{0:.3f}".format(par) for par in swarm.gbest.renormalized])))

        nptest.assert_allclose(swarm.gbest.renormalized, c, rtol=0.1, verbose=True)
        self.assertTrue(swarm.gbest.fitness.values[0] < 0.2)
        #self.assertTrue(swarm.gbest.worstErr < ErrTol or 
        #                swarm.gbest_iteration[0] == ngen-1)



if __name__ == '__main__':
    unittest.main()

