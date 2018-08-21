"""Defines a wrapper around user selectable optimisation engines.
"""
import sys
from deap.base import Toolbox
# skpar
from skpar.core.utils import get_logger
from skpar.core.evaluate import Evaluator
from skpar.core.pso import PSO
from skpar.core.pscan import PSCAN
from skpar.core.parameters import get_parameters

OPTENGINES = {'pso': PSO, 'pscan': PSCAN}

LOGGER = get_logger(__name__)

def get_optargs(userinp):
    """Parse user input for optimisation related arguments."""
    try:
        algo = userinp.get('algo', 'pso').lower()
        options = userinp.get('options', {})
        try:
            parameters = get_parameters(userinp['parameters'])
        except KeyError as exc:
            LOGGER.critical('Parameters must be defined under'\
                            'optimisation" in the input file.')
            LOGGER.critical(exc)
            sys.exit(2)
        return algo, options, parameters
    except AttributeError:
        return None


class Optimiser(object):
    """Wrapper for different optimization engines.
    """
    def __init__(self, algo, parameters, evaluate, options=None, verbose=True):
        try:
            self.optengine = OPTENGINES[algo]
        except KeyError:
            LOGGER.critical("Unsupported optimisation algorithm %s", algo)
            sys.exit(2)
        self.evaluate = evaluate
        self.parameters = parameters
        if options is None:
            options = {}
        self.optimise = OPTENGINES[algo](self.parameters, self.evaluate,
                                         **options)
        self.logger = LOGGER
        # report all tasks and objectives
        if verbose:
            log = self.logger.info
        else:
            log = self.logger.debug
        log("Algorithm: {}".format(algo))
        for item in parameters:
            log(item)

    def __call__(self, **kwargs):
        output = self.optimise(**kwargs)
        return output

    def report(self, *args, **kwargs):
        """Report optimiser state."""
        try:
            self.optimise.report(*args, **kwargs)
        except AttributeError:
            # assume optimiser does not have a report method
            pass
