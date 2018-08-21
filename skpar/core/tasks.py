"""Tasks module, defining relevant classes and functions"""
import os
import sys
from pprint import pformat, pprint
import numpy as np
from skpar.core.query import Query
from skpar.core.utils import get_logger

LOGGER = get_logger(__name__)

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
            LOGGER.critical('Task {:s} not in TASKDIR; Cannot continue'.\
                            format(task[0]))
            LOGGER.critical('Check spelling and verify import of user modules')
            LOGGER.critical('Use `usermodules: [lisf of modules]` in input')
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


class Task(object):
    """Generic wrapper over functions or executables.
    """
    def __init__(self, name, func, fargs):
        """Create a callable object from user input"""
        self.name = name
        self.func = func
        # legacy: treat last argument as kwargs if dict
        if isinstance(fargs[-1], dict):
            self.args = fargs[:-1]
            self.kwargs = fargs[-1]
        else:
            self.args = fargs
            self.kwargs = None
    #
    def __call__(self, env, database):
        """Execute the task, let caller handle any exception raised by func"""
        if self.kwargs is not None and self.args is not None:
            self.func(env, database, *self.args, **self.kwargs)
        elif self.args is not None and self.kwargs is None:
            self.func(env, database, *self.args)
        elif self.args is None and self.kwargs is not None:
            self.func(env, database, **self.kwargs)
        else:
            self.func(env, database)
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
