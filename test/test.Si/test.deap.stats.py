from deap import tools
import numpy as np

class Particle(object):
    def __init__(self, val, err):
        self.value = val
        self.error = err

fit_stats = tools.Statistics(lambda ind: ind.value)
fit_stats.register("Avg", np.mean)
fit_stats.register("Std", np.std)
fit_stats.register("Min", np.min)
fit_stats.register("Max", np.max)
# Worst Relative Error statistics
wre_stats = tools.Statistics(lambda ind: ind.error)
wre_stats.register("Min", np.min)
mstats = tools.MultiStatistics(Fitness=fit_stats, WRE=wre_stats)

pop = []
pop.append(Particle(0., 0.1))
pop.append(Particle(1., 3.0))
pop.append(Particle(1., 2.0))
pop.append(Particle(5., 5.0))

record = mstats.compile(pop)

print (record)

pop = []
pop.append(Particle(2., 0.3))
pop.append(Particle(3., 1.0))
pop.append(Particle(1., 2.5))
pop.append(Particle(5., 5.5))

record = mstats.compile(pop)

print (record)
