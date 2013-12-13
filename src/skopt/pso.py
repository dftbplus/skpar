"""
Particle swarm optimizer based on the DEAP library.
"""
import random
import operator
import numpy as np

from deap import base
from deap import creator
from deap import tools

def declareTypes(weights):
    """
    Declare Particle class with fitting objectives (-1: minimization; +1 maximization).
    Each particle consists of a set of normalised coordinates, returned by the
    particle's instance itself. The true (physical) coordinates of the particle
    are stored in the field 'renormalized'. The field 'best' contains the best 
    fitness-wise position that the particle has ever had (in normalized coords).
    Declare also Swarm class; inherit from list + PSO specific attributes
    gbest and gbestfit.
    Arguments:
        weights -- tupple, e.g. (-1,) for single objective minimization, or
                   (+1,+0.5) for two objective maximization, etc.
    """
    creator.create("pFitness", base.Fitness, weights=weights)
    creator.create("Particle", list, fitness=creator.pFitness, speed=list, past=list,
            smin=None, smax=None, best=None, norm=list, shift=list, renormalized=list,
            errors=list)
    creator.create("Swarm", list, gbest=None, gbestfit=creator.pFitness, 
                    gbest_iteration=None, gbest_maxRelErr=None)
    

def createParticle(prange):
    """
    Create particle of dimensionality len(prange), assigning initial particle
    coordinate in the i-th dimension within the prange[i] tuple.
    Note that the range is normalised and shifted, so that the result is a coordinate
    within -1 to 1 for each dimension, and initial speed between -.5 and +.5.
    To get the true (i.e. physical) coordinates of the particle, 
    one must use part.renormalized field.
    Arguments:
        prange -- list of tuples. each tuple is a range of _initial_ coord.
    Return:
        particle -- an instance of the Particle class, with initialized coordinates both
                    normalized (the instance itself) and true, physical coords (self.renormalized).
    """
    # size is the dimensionality (degrees of freedom) of the particle
    # prange is a list of tuples containing the _initial_ range of particle coordinates
    # prange is normalised, to [-1:+1], and the speedlimit is set to 0.5 the range
    size = len(prange)
    pmin,pmax,smin,smax = -1.0, 1.0, -1.0, 1.0
    part = creator.Particle(random.uniform(pmin, pmax) for _ in range(size))
    part.past = [random.uniform(pmin, pmax) for _ in range(size)]
    part.speed = [random.uniform(smin, smax) for _ in range(size)]
    part.smin = smin
    part.smax = smax
    part.norm = [(pmax-pmin)/(r[1]-r[0]) for r in prange]
    part.shift = [0.5*(r[1]+r[0]) for r in prange]
    part.renormalized = map(operator.add,map(operator.div,part,part.norm),part.shift)
    return part


def evolveParticle_0(part, best, phi1=2, phi2=2):
    """
    _NOTA__BENE_
    This is the implementation shown in the examples of the DEAP library.
    The inertial factor is 1.0 (implicit) and seems to be too big.
    Phi1/2 are also somewhat bigger than the Psi/Ki resulting from the optimal
    Psi = 2.9922
    A method to update the position and speed of a particle (part), according to the
    original PSO algorithm of Ricardo Poli, James Kennedy and Tim Blackwell, 
    'Particle swarm optimization: an overview'. Swarm Intelligence. 2007; 1: 33-57.
    Arguments:
        part -- instance of the particle class, the particle to be updated
        best -- the best known particle ever (within the life of the swarm)
        phi1,phi2 -- connectivity coefficients
    """ 
    u1 = (random.uniform(0, phi1) for _ in range(len(part)))
    u2 = (random.uniform(0, phi2) for _ in range(len(part)))
    v_u1 = list(map(operator.mul, u1, map(operator.sub, part.best, part)))
    v_u2 = list(map(operator.mul, u2, map(operator.sub, best, part)))
    part.speed = list(map(operator.add, part.speed, map(operator.add, v_u1, v_u2)))
    for i, speed in enumerate(part.speed):
        if speed < part.smin:
            part.speed[i] = part.smin
        elif speed > part.smax:
            part.speed[i] = part.smax
    part[:] = list(map(operator.add, part, part.speed))
    part.renormalized = list(map(operator.add,map(operator.div,part,part.norm),part.shift))
    
    
def evolveParticle(part, best, inertia=0.7298, acceleration=2.9922, degree = 2):
    """
    A method to update the position and speed of a particle (part), according to the
    generalized formula of Eq(3) in J.Kennedy, "Particle Swarm Optimization" in
    "Encyclopedia of Machine Learning" (2010), which is equivalent to Eqs(3-4) of
    'Particle swarm optimization: an overview'. Swarm Intelligence. 2007; 1: 33-57.
    Arguments:
        part -- instance of the particle class, the particle to be updated
        best -- the best known particle ever (within the life of the swarm)
        inertia -- factor scaling the persistence of the particle
        acceleration -- factor scaling the influence of particle connection
        degree -- unused right now. should serve for a fully informred particle swarm (FIPS),
                  but this requires best to become a list of neighbours best;
                    also u1,u2 and v_u1, v_u2 should be transformed into a Sum over neighbours
    Returns the updated particle
    """ 
    if degree != 2:
        sys.exit("ERROR: degree!=2 is not supported (no support for FIPS yet). Cannot continue.")
    # calculate persistence and influence terms
    u1 = (random.uniform(0, acceleration/degree) for _ in range(len(part)))
    u2 = (random.uniform(0, acceleration/degree) for _ in range(len(part)))
    v_u1 = list(map(operator.mul, u1, map(operator.sub, part.best, part)))
    v_u2 = list(map(operator.mul, u2, map(operator.sub, best, part)))
    persistence = list(map(operator.mul,[inertia]*len(part),map(operator.sub,part,part.past)))
    influence   = list(map(operator.add, v_u1, v_u2))
    part.speed = list(map(operator.add, persistence, influence))
    # assign current position to the old one
    for i,p in enumerate(part):
        part.past[i] = p
    # apply speed limit per dimension!
    for i, s in enumerate(part.speed):
        if s < part.smin:
            part.speed[i] = part.smin
        elif s > part.smax:
            part.speed[i] = part.smax
    # update current position in both normalized and physical coordinates
    part[:] = list(map(operator.add, part, part.speed))
    part.renormalized = map(operator.add,map(operator.div,part,part.norm),part.shift)
    

class PSO(object):
    """
    Class defining Particle-Swarm Optimizer.
    """
    toolbox = base.Toolbox()
    nBestKept = 10
    halloffame = tools.HallOfFame(nBestKept)
    
    # see J. Kennedy "Particle Swarm Optimization" in "Encyclopedia of machine learning" (2010).
    pInertia = 0.7298
    pAcceleration = 2.9922
    
    def __init__(self,npart,weights,pRange,pEval,**pEvalArgs):
        """
        Create a particle swarm
        """
        # define the particle and the methods associated with its creation, evolution and fitness evaluation
        declareTypes(weights)
        self.toolbox.register("create", createParticle, prange=pRange)
        self.toolbox.register("evolve", evolveParticle, inertia = self.pInertia, acceleration = self.pAcceleration)
        self.toolbox.register("evaluate",pEval,**pEvalArgs)
        # create a swarm from particles with the above defined properties
        self.toolbox.register("swarm", tools.initRepeat, creator.Swarm, self.toolbox.create)   
        self.swarm = self.toolbox.swarm(npart)
        # provide with statistics collector and evolution logger
        # these must be further customized, may be by directly operating on the
        # PSO instance 
        self.stats = tools.Statistics(lambda ind: ind.fitness.values)
        self.stats.register("Avg", tools.mean)
        self.stats.register("Std", tools.std)
        self.stats.register("Min", min)
        self.stats.register("Max", max)
    
        column_names = ["gen", "evals"]
        column_names.extend(self.stats.functions.keys())
        column_names.extend(["Best_maxErr",])
        self.logger = tools.EvolutionLogger(column_names)
        self.logger.logHeader()

        
    def buzz(self,ngen,ErrTol):
        """
        Let the swarm evolve for ngen generations.
        """
        gbest_gen = 0
        for g in range(ngen):
            for i,part in enumerate(self.swarm):
                iteration = (g,i)
                part.fitness.values, part.errors = self.toolbox.evaluate(part.renormalized,iteration)
                if not part.best or part.best.fitness < part.fitness:
                    part.best = creator.Particle(part)
                    part.best.fitness.values = part.fitness.values
                if not self.swarm.gbest or self.swarm.gbest.fitness < part.fitness:
                    self.swarm.gbest = creator.Particle(part)
                    self.swarm.gbest.fitness.values = part.fitness.values
                    self.swarm.gbest.renormalized = part.renormalized
                    self.swarm.gbest.errors = part.errors
                    self.swarm.gbest_iteration = iteration
                    self.swarm.gbest_maxErr = max(map(operator.abs,part.errors))
                    self.halloffame.update(self.swarm)
            # Update particles only after full evaluation of the swarm,
            # so that gbest possibly arise from the last generation.
            for part in self.swarm:
                self.toolbox.evolve(part, self.swarm.gbest)
            # Gather all the fitnesses in one list and print the stats
            self.stats.update(self.swarm)
            self.logger.logGeneration(gen=g, evals=len(self.swarm), \
                            stats=self.stats, \
                            Best_maxErr = min([max(map(operator.abs,part.errors)) for part in self.swarm]))
            # Try an alternative exit criterion
            if (self.swarm.gbest_maxErr <= ErrTol):
                break
#            print "Fitness of generation {}: {}".format(g,[p.fitness.values for p in self.swarm])
        
        return self.swarm, self.stats
