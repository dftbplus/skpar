# mandatory imports
import sys
from deap.base import Toolbox
# skopt
from skopt.core.utils import get_logger
from skopt.core.evaluate import Evaluator
from skopt.core.pso import PSO, pso_dflts, pso_args, report_stats
from skopt.core.parameters import get_parameters

optengines = {'pso': PSO}

module_logger = get_logger('skopt.optimise')

def get_optargs(spec):
    """
    """
    algo    = spec.get('algo', 'pso').lower()
    options = spec.get('options', {})
    try:
        parameters = get_parameters(spec['parameters'])
    except KeyError as exc:
        module_logger.critical('Parameters must be defined under "optimisation" in the input yaml.')
        module_logger.critical(exc)
        sys.exit(2)
    return algo, options, parameters


class Optimiser(object):
    """Wrapper for different optimization engines.
    """
    def __init__(self, algo, parameters, evaluate, *args, **kwargs):
        try:
            self.optengine = optengines[algo]
        except KeyError:
            print("Unsupported optimisation algorithm {}".format(algo))
            sys.exit(2)
        self.evaluate = evaluate
        self.parameters = parameters
        try:
            self.optimise = optengines[algo](self.parameters, self.evaluate, **kwargs)
        except KeyError:
            print("Unsupported optimisation algorithm {}".format(algo))
            sys.exit(2)

    def __call__(self, **kwargs):
        output = self.optimise(**kwargs)
        return output

    def report(self, *args, **kwargs):
        self.optimise.report(*args, **kwargs)
