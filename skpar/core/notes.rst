Generalising tasks:
======================================================================

Purpose: allow simple extensions via user modules without touching
         the main code base


Concept: 
        A task initialisation signature is:
        
        task_name(self, environment=None, identifiers=None, options=None)

        * environment is implicitly passed by the system and contains
          the overall directory setup, parameters, and iteration
          number, may be some other stuff too - e.g. parallelization
          related stuff?
        * identifiers are labels given by the user, but the system
          must translate them to proper object references and pass 
          them upon task initialisation of the task prior to
          registering it with the evaluator. Valid identifiers must
          relate to internal data structures or objects, which are
          defined upon definition of objectives. What types of objects
          one can refer to? Source dictionaries, and destination 
          dictionaries.
        * options are whatever the task comprehends but the evaluator
          and optimiser need not know about -- these are passed 
          as is upon task initialisation and thereafter not changed.

        How do we distinguish between external executables and
        functions? If task_name not in task_dictionary then think
        of it as an external executable, possibly aliased via the
        'executables' stanza in the input. 

        Can we alias functions in the same way, via the 
        'executables' stanza? It should be possible.
        May be 'executables' should become 'task_aliases'.
        The issue with aliases is that we may be able to alias an
        entire command (external_exe plus its command line options)
        and then use just the alias, without any identifiers or 
        options. ( tasks: - alias: '' )

        What if identifiers are also passed explicitly:
        * objectives
        * model_db
        model_db allows get(modelname, key) and update(modelname, key, value)
        objective allows get(objective), returning (ref, model) data

Affected areas:

in.yaml
        The way that tasks are specified
        How are tasks specified:
        task : references, options

input.py
        The way that task input is interpreted

tasks.py
        The way that tasks are executed -- straight loop; eliminate
        the if clause checking for set or plot tasks
        Task signature for initialisation and call() must incorporate
        environment variables, mutable object for potential deposit
        of results from task execution, and structure for passing 
        optional parameters for the task -- those for which the task
        itself must know about; no one else (those shall be specified
        by the user at initialisation time). The reference for the 
        mutable object for each task must be known in advance too, 
        when task is registered with evaluator. The only thing that
        tasks have to exchange with the evaluator is the updates in
        the environment -- the iteration number and the parameters.
        But the environment may assume a broader context. So 
        the environment can also become just a reference to a 
        mutable object that is registered at initialisation.
        
evaluate.py
        The way tasks are registered with the evaluator and possibly
        the call signature; If we register an 'environment' object
        initially, then the call shall not contain anything.
        The evaluator updates the environment and calls the tasks
        The tasks check the updated environment and rock.


Working with JSON input:
======================================================================
Purpose: allow json input files which are less prone to indentation
         mistakes.

Affected areas:

input.py
        Modified parse_input after introducing generalised get_input.
        Tested to work OK; see test/test_input.py


Refactor Objectives:
======================================================================
