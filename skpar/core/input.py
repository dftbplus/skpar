"""
Routines to handle the input of skpar
"""
import numpy as np
import yaml
import json
#import pprint
from collections import OrderedDict
import logging
import os
import sys
from skpar.core.utils      import normalise, get_logger
from skpar.core.objectives import set_objectives
from skpar.core.query      import Query
from skpar.core.tasks      import set_tasks, PlotTask
from skpar.core.optimise   import get_optargs

module_logger = get_logger('skpar.input')

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

def get_input(filename):
    """Read input; Exception for non-existent file.
    """
    with open(filename, 'r') as infile:
        try:
            spec = json.load(infile)
        except ValueError as exc:  # raised if input is not a valid json
        # except json.JSONDecodeError as exc: # available only python3.5 onwards
            print ('Warning: Input not a valid JSON')
            try:
                spec = yaml.load(infile)
            except yaml.YAMLError as exc:
                print ('Error: Cannot handle {} as JSON or YAML file.'.
                        format(filename))
                raise
    return spec

def parse_input(filename, verbose=False):
    """Parse input filename and return the setup
    """
    userinp = get_input(filename)
    # this should change by the introduction $variable substitution
    exedict    = userinp.get('executables', None)
    # 
    optspec    = userinp.get('optimisation', None)
    if optspec is not None:
        algo, options, parameters = get_optargs(spec['optimisation'])
        optargs = [algo, options, parameters]
        parnames = [p.name for p in parameters]
    else:
        optargs    = None
        parnames   = None
    # 
    tasksinp = userinp.get('tasks', None)
    tasks = set_tasks(tasksinp)
    #
    objectivesinp = userinp.get('objectives', None)
    objectives = set_objectives (objectivesinp, verbose=verbose)
    #
    configinp = spec.get('config', None)
    config = get_config(configinp)
    
    return tasks, objectives, optargs, config


def get_config(input):
    if input is None:
        input = {}
    config = {}
    workroot = input.get('workroot', None)
    if workroot is not None:
        workroot = os.path.abspath(os.path.expanduser(workroot))
    config['workroot'] = workroot
    templatedir = input.get('templatedir', None)
    if templatedir is not None:
        templatedir = os.path.abspath(os.path.expanduser(templatedir))
    config['templatedir'] = templatedir
    config['keepworkdirs'] = input.get('keepworkdirs', False)
    return config
