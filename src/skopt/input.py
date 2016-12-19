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
    optargs    = get_optargs    (spec['optimisation'])
    parameters = optargs[2]
    parnames = [p.name for p in parameters]
    tasks      = set_tasks      (spec['tasks'], exedict, parnames)
    objectives = set_objectives (spec['objectives'])
    return tasks, objectives, optargs
