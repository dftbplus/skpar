class Evaluate(object):
    """
    """
    import logging

    def __init__(self, paramstruct, systems=[], log = logging.getLogger(__name__)):
        """
        Here we set up the calculators and configure their defaults.
        """
        self.paramstruct = paramstruct
        self.systems = systems
        self.log = log

        self.systems = []
        for S = in systems:
            self.systems.append(S)

    def evaluate_fitness(self):
        """
        This is a dummy method. It must be substituted by the actual
        application-specific method upon instantiation of the Evaluate class.
        """
        fitness = [0.0, ] # default return value
        self.log.error("ERROR: evaluate_fitness() of {0} is not defined. Returning default value: {1}".
                format(self,fitness))
        self.fitness = fitness
        return self.fitness


    def __call__(self, parameters, iteration=None):
        """
        This translate Evaluate to a callable function that can be 
        passed to the actual optimizer.
        Parameters is likely to be a simple list of floats, rather
        than a list of Parameter instances of some class
        What we do with iteration?
        """

        # update parameters with the new guess of the optimizer
        self.paramstruct.update(parameters)
        
        # run the systems and make sure no explosions from dftb+, or plotters or analysis
        # ideally we should have consistency check of some sort... success flags or whatever.
        # i'm undecided if this should be here (very top level) or we should report and 
        # exit as soon as error could be detected - i.e. at system level, or even at calculator level.
        # per ora - fidati di me e curri, curri, montalbano!
        for sysname, system in self.systems.items():
            system(iteration)

        # do whatever analysis, and return the fitness and errors
        # note that the optimiser does not care how many deviations, => len(errors) is whatever
        # fitness must be a list, however, equal the number of objectives (not targets!)
        fitness = [1.0, ] # single objective optimization
        errors = [12, 3.5, 10] # the optimizer may optionally use max(error)<max_err for stopping

        return fitness, errors
