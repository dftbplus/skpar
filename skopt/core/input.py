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
from skopt.core.utils      import normalise, get_logger
from skopt.core.objectives import set_objectives
from skopt.core.query      import Query
from skopt.core.tasks      import set_tasks
from skopt.core.optimise   import get_optargs
from skopt.core import tasks

module_logger = get_logger('skopt.input')

def get_input_yaml(filename):
    """Read yaml input; report exception for non-existent file.
    
    """
    with open(filename, 'r') as fp:
        try:
            spec = yaml.load(fp)
        except yaml.YAMLError as exc:
            module_logger.error(exc)
            raise
    return spec

def parse_input(filename, verbose=False):
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
    #module_logger.debug("Parse input parameters: {}".format(parameters))
    #module_logger.debug("Parse input parnames  : {}".format(parnames))
    tasks      = set_tasks      (spec['tasks'], exedict, parnames)
    objectives = set_objectives (spec['objectives'], verbose=verbose)
    return tasks, objectives, optargs
