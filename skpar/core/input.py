"""
Routines to handle the input of skpar
"""
import numpy as np
import yaml
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
    # Any dependencies of tasks on objectives or vice virsa could be 
    # resolved here, before proceeding with execution
    # Plot-task depend on objectives, i.e. need references to objectives
    for task in tasks:
        if isinstance(task, PlotTask):
            task.pick_objectives(objectives)

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
