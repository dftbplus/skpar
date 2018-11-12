"""
Routines to handle the input file of skpar
"""
import os
import json
import yaml
import skpar.core.taskdict as coretd
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
    _, intype = os.path.splitext('filename')
    with open(filename, 'r') as infile:
        if intype == 'json':
            try:
                spec = json.load(infile)
            except (ValueError, json.JSONDecodeError):
            # json.JSONDecodeError is available only python3.5 onwards
                LOGGER.critical('Input not a valid JSON')
                raise
        else:
        #if intype == 'yaml':
            try:
                spec = yaml.load(infile)
            except yaml.YAMLError:
                LOGGER.warning('Input not a valid YAML')
                raise
    return spec

def parse_input(filename, verbose=True):
    """Parse input filename and return the setup
    """
    setup = {}
    userinp = get_input(filename)

    setup['config'] = get_config(userinp.get('config', None), report=True)
    setup['refdata'] = get_refdata(userinp.get('reference', None))
    setup['optimisation'] = get_optargs(userinp.get('optimisation', None))
    #
    # TASKS
    taskdict = {}
    usermodulesinp = userinp.get('usermodules', None)
    # Note the statement below emulates a yaml-like input which delivers
    # a list of [module, [list of functions]] items.
    update_taskdict(taskdict,
                    [[coretd.__name__, list(coretd.TASKDICT.keys())]])
    # Import user tasks after the core ones, to allow potential
    # replacement of `taskdict` entries with user-defined functions
    if usermodulesinp:
        update_taskdict(taskdict, usermodulesinp)
    setup['taskdict'] = taskdict
    #
    taskinp = userinp.get('tasks', None)
    tasklist = get_tasklist(taskinp)
    check_taskdict(tasklist, taskdict)
    # do trial initialisation in order to report what and how's been parsed
    # no assignment means we discard the tasks list here
    initialise_tasks(tasklist, taskdict, report=True)
    setup['tasklist'] = tasklist
    #
    # OBJECTIVES
    setup['objectives'] = set_objectives(userinp.get('objectives', None),
                                         setup['refdata'], verbose=verbose)
    #
    return setup

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
    if report:
        LOGGER.info('The following configuration was understood:')
        for key, val in config.items():
            LOGGER.info('%s: %s', key, val)
    return config
