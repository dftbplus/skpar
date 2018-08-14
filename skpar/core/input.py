"""
Routines to handle the input file of skpar
"""
import json
import yaml
from collections import OrderedDict
import os
import sys
from skpar.core.utils      import normalise, get_logger
from skpar.core.objectives import set_objectives
from skpar.core.query      import Query
from skpar.core.tasks      import set_tasks, PlotTask
from skpar.core.optimise   import get_optargs
from skpar.core.taskdict   import TASKSDICT
from skpar.core.usertasks  import update_taskdict

LOGGER = get_logger(__name__)

def get_input(filename):
    """Read input; Exception for non-existent file.
    """
    with open(filename, 'r') as infile:
        try:
            spec = yaml.load(infile)
        except (yaml.YAMLError) as exc:
            LOGGER.warning('Input not a valid YAML')
            try:
                spec = json.load(infile)
            except (ValueError, json.JSONDecodeError) as exc:
            # json.JSONDecodeError is available only python3.5 onwards
                LOGGER.critical('Cannot handle %s as JSON or YAML file.', filename)
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
    usermodulesinp = userinp.get('usermodules', None)
    taskdict = update_taskdict(usermodulesinp, taskdict)
    #
    tasksinp = userinp.get('tasks', None)
    tasks = get_tasklist(tasksinp, taskdict)
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
