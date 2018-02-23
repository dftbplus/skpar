import unittest
import numpy as np
import numpy.testing as nptest
from numpy.polynomial.polynomial import polyval
import logging
import os, sys
from skpar.core.pscan import PSCAN, pformat

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

class PscanTest(unittest.TestCase):
    """
    A small test and usage example of the PSCAN engine.
    """
    def test_scan(self):
        """Can we instantiate a pscan engine and run it?"""
        # Refdata:  5 points from a 3-rd order polynomial
        xmin,xmax = -10, 10
        nref = 5
        xref = np.linspace(xmin+1, xmax-1, nref)
        c = np.array([10, -2.5, 0.5, 0.05])
        refdata = polyval(xref, c)
        logger.debug ("Reference data: {}".format(refdata))
        refweights = np.ones(len(refdata))
        def model (par):
            coef = par + [0.05]
            return polyval(xref, coef)

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
            # on-average-required number of iterations by significantly -
            # e.g. from ~150 to ~ 110, to reduce the ErrTol
            fitness = np.atleast_1d(np.sqrt(sum(weights*np.power(errors/refdata, 2))))         
            #return fitness, np.max(np.abs(errors/refdata))
            return fitness

        # Variables specific to the optimisation problem
        # ----------------------------------------------------------------------
        # Dimensionality and range of the fitting parameters that are representted as a particle:
        # in this case, 4 polynomial coefficients are to be fitted, and we provide appropriate 
        # range for them
        # Target coef. are: 10, -2.5, 0.5, 0.05
        parameters = [(4, -10.,20.), (3, -3.,-2.), (5, 0.,2.)]
        objectives = (-1, )
        # make an instance of the pscan
        optimise = PSCAN(parameters, evaluate, objective_weights=objectives)

        # buzz the particle swarm for ngen generations 
        population, stats = optimise()

        logger.debug ("Best position sequential number: {0}".format(population.ibest))
        logger.debug ("Best position fitness: {:.5f}".format(population.best.fitness.values[0]))
        logger.debug ("Best parameter values: {}".
            format(", ".join(["{0:.3f}".format(indl) for indl in population.best])))

        # for pt in population:
        #     logger.debug(pformat(pt))

        nptest.assert_allclose(population.best, c[:3], rtol=0.1, verbose=True)
        self.assertTrue(population.best.fitness.values[0] < 0.2)

if __name__ == '__main__':
    unittest.main()


