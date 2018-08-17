"""Enable support for user-defined tasks, dynamically imported at runtime.

User can deposit his python modules in one of the following directories:

    :.:
        where skpar is invoked

    :~/.local/share/skpar/:
        must be created by user

or any other directory of his choice, or even has his python package installed.

Any function that is intended to perform a task must be listed in a dictionary
called `TASKDICT`, as 'task_name': 'callable_object' within the user module
that is to be imported by skpar at run time.
NOTE that TASKDICT is all capital letters!

:task_name:
    task name used in skpar input file

:callable object:
    the corresponding callable in the user module, that performs the task

How to specify user modules in skpar input:
    usermodules: [mod1, (mod2,path), ]

If path is not specified, the above default directories and sys.path
are checked for the named module (mod1 in the example above).


NOTE: sys.path is not ever modified; Therefore, if the user module
      contains import statements, these can only refer to modules
      that are already on sys.path, or else such imports will fail!
"""
import os
import importlib
from skpar.core.utils import get_logger

LOGGER = get_logger(__name__)

USER_MODULES_PATH = [os.path.expanduser('~/.local/share/skpar'),]

def import_user_module(name, path=None):
    """Import a user module with a given name

    If path is not given, we try direct import, and if that fails, we
    search sys.path, then '.', and the '~/.local/share/skpar' last.
    If path is given, only there we search.
    If all fails, let caller deal with it.
    """
    if path is None:
        try:
            # this will work for module on sys.path or in '.'
            module = importlib.import_module(name)
            LOGGER.info('Found module file %s', module.__file__)
            return module
        except ModuleNotFoundError:
            LOGGER.info('Module %s not installed', name)
            # prepare to search in common places
            path = USER_MODULES_PATH
    else:
        assert isinstance(path, str)
        path = [path]
    # search along path
    LOGGER.info('Looking for %s in %s', name, path)
    for filedir in path:
        if os.path.isdir(filedir):
            filepath = os.path.join(filedir, name+'.py')
            spec = importlib.util.spec_from_file_location(name, filepath)
            module = importlib.util.module_from_spec(spec)
            # this is the actual attempt to read the module file!
            try:
                spec.loader.exec_module(module)
                LOGGER.info('Found module file %s', module.__file__)
                break
            except FileNotFoundError:
                LOGGER.info('Module %s not found in %s', name, filedir)
                # continue searching along path
        else:
            LOGGER.info('Omitting %s – non existent directory', filedir)
    try:
        return module
    except NameError:
        LOGGER.info('Unable to find %s module. Cannot continue!', name)
        raise RuntimeError

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

def update_taskdict(userinp, taskdict, tag=False):
    """Update taskdict with TASKDICT from modules described in user input.

    Args:
        userinp(list): module names or tuples of (name,path)
        taskdict(dict): dictionary to be updated
        tag(bool): include module name when forming keys to be updated/inserted.

    Returns:
        None

    Raises:
        AttributeError if an imported module do not have a TASKDICT dictionary.
    """
    # Make sure we always have a list to work on, else userinp will be
    # decomposed into characters
    if isinstance(userinp, str):
        userinp = [userinp]
    modules = import_modules(userinp)
    for mod in modules:
        try:
            newdict = mod.TASKDICT
        except AttributeError:
            LOGGER.warning('Module %(name) has no TASKDICT; Ignored.',
                           name=mod.__name__)
        if not tag:
            taskdict.update(newdict)
        else:
            name = mod.__name__
            for key, val in newdict.items():
                taggedkey = '.'.join([name, key])
                taskdict[taggedkey] = val
