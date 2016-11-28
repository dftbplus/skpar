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
from skopt.tasks      import set_tasks, exedict
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
    """Parse input filename.

    Currently only yaml input is supported.
    """
    spec = get_input_yaml(filename)
    _input = []
    exedict    = spec.get('executables', None)
    tasks      = set_tasks      (spec['tasks'])
    objectives = set_objectives (spec['objectives'])
    _input.append(tasks)
    _input.append(objectives)
    return _input
