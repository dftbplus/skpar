"""Tasks module, defining relevant classes and functions"""
import sys
from skpar.core.utils import get_logger

LOGGER = get_logger(__name__)

# TODO: get_tasklist below assumes the legacy definition of tasks in userinput:
#       '- taskname: [list_of_task_arguments]'.
#       It should be possible to provide an alternative definition:
#       '- [taskname, task_argument1, .....task_argumentN]'
#       A flag in config file could allow user to select either way.
def get_tasklist(userinp):
    """Return a list of tuples of task names and task arguments."""
    if userinp is None:
        LOGGER.critical('Missing "tasks:" in user input; Nothing to do. Bye!')
        sys.exit(1)
    tasklist = []
    for item in userinp:
        # due to json/yaml specifics, a task is represented as a dictionary with
        # one item only, hence the comma after task, avoiding looping over items
        (taskname, taskargs), = item.items()
        task = (taskname, taskargs)
        tasklist.append(task)
    return tasklist

def check_taskdict(tasklist, taskdict):
    """Check task names are in the task dictionary; quit otherwise."""
    for task in tasklist:
        if task[0] not in taskdict.keys():
            LOGGER.critical('Task {:s} not in TASKDICT; Cannot continue'.\
                            format(task[0]))
            LOGGER.info('Check spelling and verify import of user modules')
            LOGGER.info('Use `usermodules: [lisf of modules]` in input')
            LOGGER.info('TASKDICT currently contains:\n\t{:s}'.\
                        format('\n\t'.join(['{:s}: {}'.format(name, func) for
                                         name, func in taskdict.items()])))
            sys.exit(1)

def initialise_tasks(tasklist, taskdict, report=False):
    """Transform a tasklist into a list of callables as per taskdict.

    Args:
        tasklist(list): a list of (task-name, user-arguments) pairs
        taskdict(dict): a dictionary mapping task names to actual functions

    Returns:
        tasks(list): callable objects, instances of Task class
    """
    LOGGER.info('Initialising tasks')
    tasks = []
    for taskname, argslist in tasklist:
        func = taskdict[taskname]
        assert isinstance(argslist, (list, tuple)),\
            ("Make sure task arguments are within []; IsString?: {}".\
             format(isinstance(argslist, str)))
        tasks.append(Task(taskname, func, argslist))

    if report:
        LOGGER.info("The following tasks will be executed at each iteration.")
        for i, task in enumerate(tasks):
            LOGGER.info("Task {:d}:\t{:s}".format(i, task.__repr__()))
    return tasks


class Task():
    """Generic wrapper over functions or executables.
    """
    def __init__(self, name, func, fargs):
        """Create a callable object from user input.

        Note: `fargs` are user defined function arguments.
              The function call via the __call__() method of this class allows
              for other arguments to be passed by the caller.

        Note: `fargs` is parsed so that if the last item in the list is a dict,
              then fargs[-1] becomes **kwargs while fargs[:-1] becomes *args
              for the function call

        Args:
            name(str): name of the task (to appear in logs)
            func(callable): the function being called by __call__()
            fargs(list): list of arguments to be passed to func.
        """
        self.name = name
        self.func = func
        # treat last argument as kwargs if dict
        if isinstance(fargs[-1], dict):
            self.args = fargs[:-1]
            self.kwargs = fargs[-1]
        else:
            self.args = fargs
            self.kwargs = {}
    #
    def __call__(self, env, database):
        """Execute the task, let caller handle any exception raised by func

        Args:
            env(dict): a dictionary with implicitly passed args
            database(object or dict): a database object serving for data
                                      exchange
        """
        self.func(env, database, *self.args, **self.kwargs)
    #
    def __repr__(self):
        """Yield a summary of the task.
        """
        srepr = []
        srepr.append('{:s}: {}'.format(self.name, self.func))
        if self.args:
            srepr.append('\t\t\t  {:d} args: {:s}'.format(len(self.args),
                ', '.join(['{}'.format(str(arg)) for arg in self.args])))
        if self.kwargs:
            srepr.append('\t\t\t{:d} kwargs: {:s}'.format(len(self.kwargs.keys()),
               ', '.join(['{}: {}'.format(key, val) for key, val in
                          self.kwargs.items()])))
        return "\n".join(srepr)
