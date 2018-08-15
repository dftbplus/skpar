"""
Routines to handle the input file of skpar
"""
import json
import yaml
import os
from skpar.core.utils      import normalise, get_logger
from skpar.core.objectives import set_objectives
from skpar.core.query      import Query
from skpar.core.tasks      import get_tasklist, check_tasks
from skpar.core.optimise   import get_optargs
#from skpar.core.taskdict   import TASKDICT
from skpar.core.usertasks  import update_taskdict

LOGGER = get_logger(__name__)

def get_input(filename):
    """Read input; Exception for non-existent file.
    """
    with open(filename, 'r') as infile:
        try:
            spec = yaml.load(infile)
        except yaml.YAMLError:
            LOGGER.warning('Input not a valid YAML')
            try:
                spec = json.load(infile)
            except (ValueError, json.JSONDecodeError) as exc:
            # json.JSONDecodeError is available only python3.5 onwards
                LOGGER.critical('Cannot handle %s as JSON or YAML file.',
                                filename)
                raise
    return spec

def parse_input(filename, verbose=False):
    """Parse input filename and return the setup
    """
    userinp = get_input(filename)
    #
    optinp = userinp.get('optimisation', None)
    optimisation = get_optargs(optinp)
    #
    taskdict = {}
    usermodulesinp = userinp.get('usermodules', None)
    update_taskdict(usermodulesinp, taskdict)
    update_taskdict('skpar.core.taskdict', taskdict)
    update_taskdict('skpar.dftbutils.taskdict', taskdict)
    #
    taskinp = userinp.get('tasks', None)
    tasklist = get_tasklist(taskinp)
    check_tasks(tasklist, taskdict)
    #
    objectivesinp = userinp.get('objectives', None)
    objectives = set_objectives(objectivesinp, verbose=verbose)
    #
    configinp = userinp.get('config', None)
    config = get_config(configinp)
    #
    return taskdict, tasklist, objectives, optimisation, config

def get_config(userinp):
    """Parse the arguments of 'config' key in user input"""
    if userinp is None:
        userinp = {}
    config = {}
    workroot = userinp.get('workroot', None)
    if workroot is not None:
        workroot = os.path.abspath(os.path.expanduser(workroot))
    config['workroot'] = workroot
    templatedir = userinp.get('templatedir', None)
    if templatedir is not None:
        templatedir = os.path.abspath(os.path.expanduser(templatedir))
    config['templatedir'] = templatedir
    config['keepworkdirs'] = userinp.get('keepworkdirs', False)
    return config
