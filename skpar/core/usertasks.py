"""Enable support for user-defined tasks, dynamically imported at runtime.


Any function that is intended to perform a task must be present as a
'task_name': 'callable_object' item in a dictionary called `TASKDICT` in the
user module that is to be imported by skpar at run time.

The desired TASKDICT should be ideally inside an installed package.
Alternatively, modules must be found using the standard Python import mechanism,
i.e. must be placed along sys.path.

.. note:: sys.path is not ever modified; consider using PYTHONPATH in the shell

:task_name:
    task name used in the ``tasks`` section the input file

:callable object:
    the corresponding callable in the user module, that performs the task

.. note:: that TASKDICT is all capital letters!


There are three ways to import tasks from user modules, as per example below:

.. code:: yaml

    usermodules:
        # 1
        - mypackage.amodule
        # 2
        - [mypackage.amodule, alias]
        # 3
        - [mypackage.amodule, [taskname1, taskname2, ]]

Each of the three cases mandates different ways to refer to the tasks later in
the ``tasks`` section:

    1. mypackage.amodule.taskname : ....

    2. alias.taskname : ....

    3. taskname1 : ....

.. note:: The third case allows to overwrite core skpar tasks.

"""
from importlib import import_module
from skpar.core.utils import get_logger

LOGGER = get_logger(__name__)

def import_taskdict(modname):
    """Import user module and return its name and TASKDICT"""
    try:
        mod = import_module(modname)
    except (ImportError, ModuleNotFoundError):
        LOGGER.critical('Module %s not found. '
                        'Check it is along PYTHONPATH', modname)
        raise
    try:
        modtd = getattr(mod, 'TASKDICT')
    except AttributeError:
        LOGGER.critical('Module %s has no TASKDICT; '
                        'Please, remove it from input, to continue.',
                        mod.__name__)
        raise
    return mod.__name__, modtd

def tag_dictkeys(tag, dictionary):
    """Return the dictionary with tagged keys of the form 'tag.key'"""
    tagged = {}
    for key, val in dictionary.items():
        tagged[tag+'.'+key] = val
    return tagged

def update_taskdict(taskdict, userinp):
    """Update taskdict with tasks from modules described in user input.

    Provides support for the following userinp:

    .. code:: yaml

        usermodules:
            #
            # user must use modulename.taskname in tasks section
            - modulename
            #
            # user must use modulealias.taskname in tasks section
            - [modulename, modulealias]
            #
            # user must use taskname only in tasks section
            - [modulename, [taskname1, taskname2, ...]]

    Args:
        taskdict(dict): dictionary to be updated
        userinp(list or str): list of modules or a string (single module)

    Returns:
        None

    Raises:
        AttributeError if an explicit task is not found in user's module TASKDICT
    """
    # Make sure we always have a list to work on, else userinp is a string,
    # and will be decomposed into characters
    if isinstance(userinp, str):
        userinp = [userinp]
    for item in userinp:
        if not isinstance(item, list):
            # treat as a module name; get all tasks
            modname, modtd = import_taskdict(item)
            taskdict.update(tag_dictkeys(modname, modtd))
        else:
            modname, modtd = import_taskdict(item[0])
            if isinstance(item[1], list):
                # an explicit list of task names to import; do not tag
                for key in item[1]:
                    try:
                        taskdict[key] = modtd[key]
                    except KeyError:
                        LOGGER.critical("Task name %s not in %s's TASKDICT",
                                        key, modname)
                        raise
            else:
                # alias the module name
                taskdict.update(tag_dictkeys(item[1], modtd))
