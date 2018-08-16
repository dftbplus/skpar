"""
Routines to handle the input file of skpar
"""
import os
import json
import yaml
from skpar.core.utils      import get_logger
from skpar.core.objectives import set_objectives
from skpar.core.tasks      import get_tasklist, check_tasks
from skpar.core.optimise   import get_optargs
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
            except (ValueError, json.JSONDecodeError):
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
    configinp = userinp.get('config', None)
    config = get_config(configinp)
    #
    optinp = userinp.get('optimisation', None)
    optimisation = get_optargs(optinp)
    #
    taskdict = {}
    usermodulesinp = userinp.get('usermodules', None)
    # Tag the tasks from user modules like modulename.taskname
    tag = config['tagimports']
    if usermodulesinp:
        update_taskdict(usermodulesinp, taskdict, tag=tag)
    update_taskdict('skpar.core.taskdict', taskdict)
    #
    taskinp = userinp.get('tasks', None)
    tasklist = get_tasklist(taskinp)
    check_tasks(tasklist, taskdict)
    #
    objectivesinp = userinp.get('objectives', None)
    objectives = set_objectives(objectivesinp, verbose=verbose)
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
    config['tagimports'] = userinp.get('tagimports', True)
    return config
