"""Enable support for user-defined tasks, dynamically imported at runtime.

User can deposit his python modules in one of the following directories:

    :.:
        where skpar is invoked

    :~/.local/share/skpar/:
        must be created by user

or any other directory of his choice, or even has his python package installed.

Any function that is intended to perform a task must be listed in a dictionary
called `taskdict`, as 'task_name': 'callable_object' within the user module
that is to be imported by skpar at run time.

:task_name:
    task name used in skpar input file

:callable object:
    the corresponding callable in the user module, that performs the task

How to specify user modules in skpar input:
    usermodules: [mod1, (mod2,path), ]

If path is not specified, sys.path and the above default directories
are checked for the named module (mod1 in the example above).
"""
import os
import sys
import imp
from skpar.core.utils import get_logger

LOGGER = get_logger(__name__)

USER_MODULES_PATH = ['.', os.path.expanduser('~/.local/share/skpar')]

def import_user_module(name, path=None):
    """Import a user module with a given name

    If path is not given, sys.modules is checked first,
    then '.' and the '~/.local/share/skpar' directories in that order.
    If this fails, let caller deal with it.
    """
    if path is None:
        # Suppose user may have the module along sys.path
        try:
            return sys.modules[name]
        except KeyError:
            pass
        # But if not installed, and no path, then search in common places
        path = USER_MODULES_PATH
        LOGGER.info('Looking for user modules in %s', path)
    else:
        if isinstance(path, str):
            path = [path]
    fmod, pathname, description = imp.find_module(name, path)
    LOGGER.info('Found user module: %s in %s', fmod, pathname)

    try:
        return imp.load_module(name, fmod, pathname, description)
    finally:
        # Since we may exit via an exception, close fmod explicitly.
        if fmod:
            fmod.close()

def import_modules(namelist):
    """Import user modules as specified in the name list.
    """
    modules = []
    for item in namelist:
        try:
            name, path = item
        except ValueError:
            name, path = (item, None)
        modules.append(import_user_module(name, path))
    return modules

def update_taskdict(userinp, taskdict):
    """Update taskdict with tasks from user modules
    """
    modules = import_modules(userinp)
    for mod in modules:
        try:
            taskdict = taskdict.update(mod.taskdict)
        except AttributeError:
            LOGGER.warning('User module %(name) has no taskdict and is ignored.',
                           name=mod.__name__)
    return taskdict
