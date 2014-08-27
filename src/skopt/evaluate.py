"""
"""
import logging

class Evaluate:
    """
    callable class that is the only connection between the optimizer and the
    actual calculations/plotting/analysis etc
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
        for S in systems:
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
        This translates Evaluate to a callable function that can be 
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

def relerr(calc,ref):
    """
    """
    if ref == 0:
        if calc == 0:
            result = 0
        else :
            result = 1
    else:
        result = (calc-ref)/ref
    return result

def evaluate_residues(targets,calculated,verbose=True,log=logging.getLogger(__name__)):
    """ 
    Evaluate the individual deviation, in absolute and relrative terms, as well as the
    RMS deviation, between calculated results and target.
    Requires that calculated is of the same length as targets.
    targets (see targets.py) is supposed to be a list like class, list of tupples,
    with additional attribute being weight. The weight is important only for RMSDeviations
    and is not used in this particular routine.
    """
    import numpy as np

    residues = [t[1] - calculated[i][1] for i,t in enumerate(targets)]
    RelDev = [100.*np.abs(r/t[1]) for r,t in zip(residues,targets)]
    summary = [(t,calculated[i][1],residues[i],RelDev[i]) for i,t in enumerate(targets)]
    if verbose:
        log.info("\tTarget, Calc. Value, Residue, RelDev(%):\n\t\t"+\
                "\n\t\t".join(["{t:13s}:  {tval:8.3f}  {cval:8.3f}  {r:8.3f}  {e:8.1f}".\
                format(t=s[0][0],tval=s[0][1],cval=s[1],r=s[2],e=s[3]) for s in summary]))
    
    return residues, RelDev

def evaluate_RMSD(targets,calculated,verbose=False,log=logging.getLogger(__name__)):
    """ 
    Evaluate the individual deviation, in absolute and relative terms, as well as the
    RMS deviation, between calculated results and target.
    Requires that calculated is of the same length as targets.
    targets (see targets.py) is supposed to be a list like class, list of tupples,
    with additional attribute being weight. The weight is important only for RMSDeviations.
    """
    import numpy as np

    residues = [t[1] - calculated[i][1] for i,t in enumerate(targets)]
    RMSDev = np.sqrt(sum([t.weight*(r**2) for r,t in zip(residues,targets)]))
    RelDev = [100.*np.abs(r/t[1]) for r,t in zip(residues,targets)]
    summary = [(t,calculated[i][1],residues[i],RelDev[i]) for i,t in enumerate(targets)]
    if verbose:
        log.info("\tTarget, Calc. Value, Residue, RelDev(%):\n\t\t"+\
                "\n\t\t".join(["{t:13s}:  {tval:8.3f}  {cval:8.3f}  {r:8.3f}  {e:8.1f}".\
                format(t=s[0][0],tval=s[0][1],cval=s[1],r=s[2],e=s[3]) for s in summary]))
    log.info("\tRMSDev: {rms}".format(rms=RMSDev))
    
    return (RMSDev,), residues, RelDev

def evaluate_RMSD_multysyst(targetvalues,calcvalues,targetweights,systemweights,
                            verbose=False,log=logging.getLogger(__name__)):
    """ 
    Evaluate the individual deviation, in absolute and relrative terms, as well as the
    RMS deviation, between calculated results and targets.
    targetvalues, calculated values, and targetweights are lists of lists of floats.
    systemweights is a lists of floats, its length equal the number of lists e.g. in 
    targetvalues; these should match accross targets, weights and calculated.
    """
    import numpy as np

    residues = [t[1] - calculated[i][1] for i,t in enumerate(targets)]
    RMSDev = np.sqrt(sum([t.weight*(r**2) for r,t in zip(residues,targets)]))
    RelDev = [100.*np.abs(r/t[1]) for r,t in zip(residues,targets)]
    summary = [(t,calculated[i][1],residues[i],RelDev[i]) for i,t in enumerate(targets)]
    if verbose:
        log.info("\tTarget, Calc. Value, Residue, RelDev(%):\n\t\t"+\
                "\n\t\t".join(["{t:13s}:  {tval:8.3f}  {cval:8.3f}  {r:8.3f}  {e:8.1f}".\
                format(t=s[0][0],tval=s[0][1],cval=s[1],r=s[2],e=s[3]) for s in summary]))
    log.info("\tRMSDev: {rms}".format(rms=RMSDev))
    
    return (RMSDev,), residues, RelDev
