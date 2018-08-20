"""Test particle swarm optimisation module"""
import unittest
import logging
import numpy as np
import numpy.testing as nptest
from numpy.polynomial.polynomial import polyval
from deap import base
from deap import creator
from skpar.core.pso import PSO, createParticle, evolveParticle, pformat

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
LOGGER = logging.getLogger(__name__)

class PSOTest(unittest.TestCase):
    """
    A small test and usage example of the PSO engine.
    """
    def test_pso(self):
        """Can we instantiate a PSO and run it?"""
        # Refdata:  5 points from a 3-rd order polynomial
        xmin, xmax = -10, 10
        nref = 5
        xref = np.linspace(xmin+1, xmax-1, nref)
        coef = np.array([10, -2.5, 0.5, 0.05])
        refdata = polyval(xref, coef)
        LOGGER.debug("Reference data: {}".format(refdata))
        refweights = np.ones(len(refdata))
        def model(par):
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
            errors = refdata - modeldata
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
        prange = [(-20, 20), (-5, 5), (-2, 2), (-1, 1)]
        # Setup the PSO for single objective (one-tuple) minimisation (negative sign)
        # The engine is capable of handling multiple objectives, but this may be
        # explored at a later stage. Here we have scalarised everything in advance.
        objectives = (-1, )
        # number of particles composing the swarm
        npart = 8
        # max number of generations through which the swarm evolves
        ngen = 150
        # make an instance of the pso
        #pso = PSO(prange, evaluate, objectives=objectives, npart=npart)
        pso = PSO(prange, evaluate, npart=npart, objective_weights=objectives,
                  ngen = ngen)

        # buzz the particle swarm for ngen generations
        swarm, stats = pso()

        LOGGER.debug ("gbest iteration: {0}".format(swarm.gbest_iteration))
        LOGGER.debug ("gbest fitness: {:.5f}".format(swarm.gbest.fitness.values[0]))
        LOGGER.debug ("Fitted coefficients: {}".\
                      format(", ".join(["{0:.3f}".format(par)\
                                        for par in swarm.gbest.renormalized])))

        nptest.assert_allclose(swarm.gbest.renormalized, coef, rtol=0.1,
                               verbose=True)
        self.assertTrue(swarm.gbest.fitness.values[0] < 0.2)

class ParticleTest(unittest.TestCase):
    """Test creation and evolution of particles for the PSO
    """
    def test_create_particle(self):
        """Can we create a particle?"""
        # 1D particle
        creator.create("pFitness", base.Fitness, weights=(1,))
        creator.create("Particle", list, fitness=creator.pFitness, speed=list, past=list,
            smin=None, smax=None, best=None, norm=list, shift=list, renormalized=list,
            strict_bounds=True, prange=list)
        prange = [[0, 2]]
        p1 = createParticle(prange)
        self.assertTrue(-1. <= p1[0] <= 1.)
        print('\nCreated P1: {}'.format(prange))
        print(pformat(p1))
        # 2D particle
        prange = [[0, 2], [-3, 3]]
        p2 = createParticle(prange)
        self.assertTrue(-1. <= p2[0] <= 1.)
        self.assertTrue(-1. <= p2[1] <= 1.)
        print('\nCreated P2: {}'.format(prange))
        print(pformat(p2))

    def test_evolve_particle_escape(self):
        """Can we evolve the particle and let it escape the initial range?"""
        creator.create("pFitness", base.Fitness, weights=(1,))
        creator.create("Particle", list, fitness=creator.pFitness, speed=list, past=list,
                   smin=None, smax=None, best=None, norm=list, shift=list, renormalized=list,
                   strict_bounds=True, prange=list)
        # 1D particle
        prange = [[0, 2]]
        p1 = createParticle(prange, strict_bounds=False)
        p1.best = [0.8,]
        self.assertTrue(-1. <= p1[0] <= 1.)
        print('\nCreated P1: {}'.format(prange))
        print(pformat(p1))
        gbest = [3,]
        evolveParticle(p1, gbest)
        print('\nEvolution 1: P1: {}'.format(prange))
        print(pformat(p1))
        evolveParticle(p1, gbest)
        print('\nEvolution 2: P1: {}'.format(prange))
        print(pformat(p1))
        self.assertTrue(p1[0] > 1)

    def test_evolve_strict_bounds(self):
        """Can we evolve the particle but maintaining strict bounds?"""
        creator.create("pFitness", base.Fitness, weights=(1,))
        creator.create("Particle", list, fitness=creator.pFitness, speed=list, past=list,
                   smin=None, smax=None, best=None, norm=list, shift=list, renormalized=list,
                   strict_bounds=True, prange=list)
        # 1D particle
        prange = [[0, 2]]
        p1 = createParticle(prange, strict_bounds=True)
        p1.best = [0.8,]
        self.assertTrue(all([-1. <= pp <= 1. for pp in p1]))
        print('\nCreated P1: {}'.format(id(p1)))
        print(pformat(p1))
        gbest = [3,]

        print('\nEvolution 1 -- P1: {}'.format(id(p1)))
        evolveParticle(p1, gbest)
        print(pformat(p1))

        print('\nEvolution 2 -- P1: {}'.format(id(p1)))
        evolveParticle(p1, gbest)
        print(id(p1))
        print(pformat(p1))
        self.assertTrue(all([-1. <= pp <= 1. for pp in p1]))
        self.assertTrue(all([rr[0] <= pp <= rr[1] for pp, rr in zip(p1.renormalized, prange)]))

        print('\nEvolution 3 -- P1: {}'.format(id(p1)))
        evolveParticle(p1, gbest)
        print(id(p1))
        print(pformat(p1))
        self.assertTrue(all([-1. <= pp <= 1. for pp in p1]))
        self.assertTrue(all([rr[0] <= pp <= rr[1] for pp, rr in zip(p1.renormalized, prange)]))

if __name__ == '__main__':
    unittest.main()

