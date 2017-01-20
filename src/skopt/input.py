"""
Routines to handle the input of skopt
"""
import numpy as np
import yaml
#import pprint
from collections import OrderedDict
import logging
import os
import sys
from skopt.utils      import normalise
from skopt.objectives import set_objectives
from skopt.query      import Query
from skopt.tasks      import set_tasks
from skopt.optimise   import get_optargs
from skopt import tasks

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

def get_input_yaml(filename):
    """Read yaml input; report exception for non-existent file.
    
    """
    with open(filename, 'r') as fp:
        try:
            spec = yaml.load(fp)
        except yaml.YAMLError as exc:
            # this should go to a logger...?
            print (exc)
    return spec

def parse_input(filename):
    """Parse input filename and return the setup

    Currently only yaml input is supported.
    """
    spec = get_input_yaml(filename)
    exedict    = spec.get('executables', None)
    optspec    = spec.get('optimisation', None)
    if optspec is not None:
        algo, options, parameters = get_optargs(spec['optimisation'])
        optargs = [algo, options, parameters]
        parnames = [p.name for p in parameters]
    else:
        optargs    = None
        parnames   = None
    # TODO: revisit the initialisation of tasks.
    # Current implementation here is not very neat for two reasons:
    # the interpretation of the input spec requires prior interpretation 
    # of other spec. Parsing of the input should be independent of subsequent
    # setup stuff, and these typically are separate.
    #logger.debug("Parse input parameters: {}".format(parameters))
    #logger.debug("Parse input parnames  : {}".format(parnames))
    tasks      = set_tasks      (spec['tasks'], exedict, parnames)
    objectives = set_objectives (spec['objectives'])
    return tasks, objectives, optargs
