Generalising tasks:
======================================================================

Purpose: 
--------------------------------------------------
Allow simple extensions via user modules without touching
the main code base

Concept: 
--------------------------------------------------
Taks are now very simpler objects, holding a name,
corresponding callable, and user arguments to be
passed to the task.
They have a __call__(), during which implicit args
from the caller are passed: environment dictionary
and, database (reference?).
So the actual call to the function corresonding to
the task is:
func(environment, database, *useraargs, **userkwargs)
Since in yaml/json we cannot specify **kwargs, we 
parse the userargs and make userargs[-1] into
userkwargs. All mapping arguments can be passed this
way to the user function, and the ones not explicitly
used are passed to further callables inside the function.
This enables to pass arguments to np.loadtxt or to
matplotlib, or to subprocess.check_call etc.

Aliases:
--------------------------------------------------
    Support for these is dropped at present.
    Better to introduce $var instead of old 
    implementation, to avoid surprises where user
    decide to use an identifier that was already
    defined as an alias, leading to random behaviour.


Parallelism:
--------------------------------------------------
    Task now acquire environment data at call time.
    No variable items are held during their 
    initialisation.
    Tasks are now instantiated inside the call of
    the evaluator, so that multiple evaluations 
    (hence multiple instances of the same task)
    can be run with different parameters at the same
    time.


What tasks we can have:
--------------------------------------------------
:executables:
    task name is 'execute'
    task arguments: executable, command-line arguments
    executed via os.subprocess 

:core functions:
    task name is the function name
    task arguments are the function arguments
    called directly
    part of the code
    declared in task_dictionary
    

:user functions:
    task name is the function name
    task arguments are the function arguments
    called directly
    imported via implib, see usertasks.py
    usertasks.py must contain TASKDICT
    which will update (potentially could replace) 
    the global task dict.
    declared in task_dictionary



Working with JSON input:
======================================================================
Done.



Refactor Objectives:
======================================================================



Parameters:
======================================================================
Parameter values are now passed to evaluator who does not hold any 
reference to the original Parameters list established during parsing 
of user input.
Evaluator now holds only parameter names. 
Both these points are mandatory to enable parallel calls to evaluator.
