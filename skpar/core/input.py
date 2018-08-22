"""
Routines to handle the input file of skpar
"""
import os
import json
import yaml
from skpar.core.utils      import get_logger
from skpar.core.objectives import set_objectives
from skpar.core.tasks      import get_tasklist, check_taskdict
from skpar.core.tasks      import initialise_tasks
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

def parse_input(filename, verbose=True):
    """Parse input filename and return the setup
    """
    userinp = get_input(filename)
    #
    # CONFIG
    configinp = userinp.get('config', None)
    config = get_config(configinp, report=True)
    #
    # OPTIMISATION
    optinp = userinp.get('optimisation', None)
    optimisation = get_optargs(optinp)
    #
    # TASKS
    taskdict = {}
    usermodulesinp = userinp.get('usermodules', None)
    update_taskdict(taskdict, 'skpar.core.taskdict', tag=False)
    # Import user tasks after the core ones, to allow potential
    # replacement of `taskdict` entries with user-defined functions
    # if `tagimports` is false.
    tag = config['tagimports']
    if usermodulesinp:
        update_taskdict(taskdict, usermodulesinp, tag=tag)
    #
    taskinp = userinp.get('tasks', None)
    tasklist = get_tasklist(taskinp)
    check_taskdict(tasklist, taskdict)
    # do trial initialisation in order to report what and how's been parsed
    # no assignment means we discard the tasks list here
    initialise_tasks(tasklist, taskdict, report=True)
    #
    # OBJECTIVES
    objectivesinp = userinp.get('objectives', None)
    objectives = set_objectives(objectivesinp, verbose=verbose)
    #
    return taskdict, tasklist, objectives, optimisation, config

def get_config(userinp, report=True):
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
    # related to interpretation of input file
    config['tagimports'] = userinp.get('tagimports', True)
    if report:
        LOGGER.info('The following configuration was understood:')
        for key, val in config.items():
            LOGGER.info('%s: %s', key, val)
    return config
