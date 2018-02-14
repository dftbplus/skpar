"""
Parameter Scanner (PSCAN)
======================================================================

This module realises a linear scan of the parameter space.
It creates a grid of points based on user input of parameter range and
number of points for discretising the range. The grid is made with 
the help of numpy.linspace. 

There is an implicit assumption in how parameter definition is
interpreted at present, which is merely to avoid modifying the 
parameters-related classes and functions. 
The assumption is that parameter value is interpreted as number of
points for the scan over the range of the given parameter.
Note that an initialisation value makes no sense for the scan.
Therefore the above assumptions is safe.
The interpretation of min/max parameter values remains the same as 
usual.

While there is no encoded limitation on the number of parameters to 
use in a scan, practically, for more than 2 or three parameters, the
computational effort will be excessive, in comparison to optimisation
based on the PSO.
"""
import numpy as np
from deap import base
from deap import creator
from deap import tools
from skpar.core.utils import get_logger

module_logger = get_logger('skpar.pscan')

def declareTypes(weights=(-1,)):
    """Declare a types relevant to PSCAN.
    """
    creator.create("pFitness", base.Fitness, weights=weights)
    creator.create("Population", list, inext=None, best=None, ibest=None)
    creator.create("Point", list, ind=None, fitness=creator.pFitness)

def create_positions(ranges, numpts):
    """Create a sequence of np.prod(nupmts) over the ranges.
    
    Args:
        ranges: list of 2-tuples, each tuple being [min, max] of a numerical range.
        numpts: list of integers -- the number of equally spaced points 
                between [min, max] including the end points.
    Returns:
        A sequence of all points on the multidimensional grid formed by
        numpts along each of ranges. Note that NOT a grid structure, but
        a linear sequence is returned, i.e. a list of N-tuples, each tuple
        being the coordinate of a point, N being the number of ranges.
        Numpy linspace is underlying the division of the ranges, end-points
        inclusive.
    """
    linsp = []
    for rng, num in zip(ranges, numpts):
        linsp.append(np.linspace(rng[0], rng[1], num=int(num), endpoint=True))
    grid = np.meshgrid(*linsp, sparse=False)    # list of arrays making up the grid
    _positions = np.vstack(map(np.ravel, grid)) # this creates list of lists (one per direction)
    positions = list(zip(*_positions))          # now we have a sequence of tuples
    return positions

def create_point(positions, ind):
    """Return a Point object from a sequence of positions, assigning an index.

    Args:
        positions: a sequence
        ind: an integer

    Returns:
        Return a Point object from the ind-th position of `positions`.
    """
    pt = creator.Point(positions[ind])
    pt.ind = ind
    return pt

def pformat(point):
    """Return a formatted string for printing all info of a Point object.
    """
    ss = []
    ss.append('Position:  {}'.format(' '.join(['{:<7.3f}'.format(item) for item in point])))
    ss.append('Index:     {:<7d}'.format(point.ind))
    ss.append('Fitness:   {}'.format(point.fitness))
    return '\n'.join(ss)

def create_population(positions):
    """Return a Population object of Point objects from a sequence of positions.

    Reset the 'inext' index to 0.
    """
    population = creator.Population([create_point(positions, ind) 
                                     for ind in range(len(positions))])
    population.inext = 0
    return population

def report_stats(stats):
    """
    """
    logger = module_logger
    statsHeader = "".join([
    '{0:>10s}'.format('Min.'),
    '{0:>10s}'.format('Max.'),
    '{0:>10s}'.format('Avg.'),
    '{0:>10s}'.format('Std.'),
    ])
    logger.info('')
    logger.info("Fitness statistics follow:")
    logger.info(statsHeader)
    logger.info('============================================================')
    s = stats[0]
    logger.info("".join([
    '{0:>10.4f}'.format(s['Fitness']['Min']),
    '{0:>10.4f}'.format(s['Fitness']['Max']),
    '{0:>10.4f}'.format(s['Fitness']['Avg']),
    '{0:>10.4f}'.format(s['Fitness']['Std']),
        ]))
    logger.info('============================================================')



class PSCAN(object):
    """Class defining a scanner over a set of positions.

    Executing it performs a linear scan over the parameter space by dividing 
    the range of each parameter in a number points as dictated by user.
    The resulting sequence of points is scanned linearly, i.e. point by point.

    There is an implicit assumption in how parameter definition is
    interpreted at present, which is merely to avoid modifying the 
    parameters-related classes and functions. 
    The assumption is that parameter value is interpreted as number of
    points for the scan over the range of the given parameter.
    Note that an initialisation value makes no sense for the scan.
    Therefore the above assumptions is safe.
    The interpretation of min/max parameter values remains the same as 
    usual.
    """
    toolbox = base.Toolbox()
    nBestKept = 10
    halloffame = tools.HallOfFame(nBestKept)
    
    def __init__(self, parameters, evaluate, objective_weights=(-1,), *args, **kwargs):
        """Create a set of positions to scan over based on given parameters.
        """
        self.logger = module_logger
        self.logger.debug("Working with the following parameters:")
        # try to establish the names of the parameters for logging
        try:
            self.parnames = [p.name for p in parameters]
        except AttributeError:
            self.parnames = None
        # try to establish the allowed parameter range
        try:
            ranges = [(p.minv, p.maxv) for p in parameters]
            numpts = [int(p.value) for p in parameters]
        except AttributeError:
            assert isinstance(parameters, list) and len(parameters[0]) == 3,\
                ("NOTABENE: `parameters` argument of PSCAN.__init__() should be a list,\n"
                "every element of which is either a 3-tuple "
                "(numpts, min_value, max_value)\n"
                "or a class with attributes value, minv and maxv, where the \n"
                "value is interpreted as number of points over [minv, maxv]")
            numpts = [p[0] for p in parameters]
            ranges = [(p[1], p[2]) for p in parameters]
        # declare the Point type and the methods associated with it
        declareTypes(objective_weights)
        # create a sequence of points on the grid to sample
        # treat the parameter.value as the desired number of points to scan
        positions = create_positions(ranges, numpts)
        # register the methods to obtain a point and evaluate it
        self.toolbox.register('create', create_point, positions=positions)
        self.toolbox.register('population', create_population, positions=positions)
        self.toolbox.register('evaluate', evaluate)
        self.population = self.toolbox.population()
        # Provide statistics collector (fitness statistics)
        fit_stats = tools.Statistics(key=lambda ind: ind.fitness.values)
        fit_stats.register("Avg", np.mean)
        fit_stats.register("Std", np.std)
        fit_stats.register("Min", np.min)
        fit_stats.register("Max", np.max)
        self.mstats = tools.MultiStatistics(Fitness=fit_stats)
        self.stats_record = []
        
    def optimise(self):
        """Let the scan process execute, looping over all points.
        """
        for ind, pos in enumerate(self.population):
            self.population.inext = ind + 1
            pos.fitness.values = self.toolbox.evaluate(pos, ind)
            if not self.population.best or self.population.best.fitness < pos.fitness:
                self.population.ibest = pos.ind
                self.population.best = self.toolbox.create(ind=ind)
                self.population.best.fitness = pos.fitness
                self.halloffame.update(self.population)
        self.stats_record.append(self.mstats.compile(self.population))
        return self.population, self.stats_record
            
    def report(self):
        report_stats(self.stats_record)
        self.logger.info("Best position    : {}".format(self.population.ibest))
        self.logger.info("Best fitness     : {}".format(self.population.best.fitness.values))
        if self.parnames:
            self.logger.info("Best parameters:\n"+
                "\n".join(["{:>20s}  {}".format(name, val) 
                for (name, val) in zip(self.parnames, self.population.best)]))
        else:
            self.logger.info("Best parameters  : {}".format(self.population.best))

    def __call__(self, *args, **kwargs):
        return self.optimise(*args, **kwargs)
