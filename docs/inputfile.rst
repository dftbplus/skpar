======================================================================
SKOPT Input File
======================================================================

SKOPT is controlled by an input file in `YAML`_.

The input file must contain at least the following sections:

-  ``systems``: 
    Self-contained, abstract units, encapsulating *reference data* and 
    *tasks*. The *tasks* comprise the model in an abstract sense.
    In practical terms and in the context of DFTB parameter optimisation, 
    a *system* would be an atomic structure, on which a series of 
    DFTB calculations and subsequent analysis are performed -- referred
    to as *tasks* -- in order to obtain the quantities of interest
    stated in the *reference data*. The execution of the tasks is
    essentially the execution of the abstract model.

Optional sections:

* ``refdata``: 
    Reference data used to compose objectives that are not 
    associated with a particular *system*.

* ``tasks``: 
    Tasks that are added to the model in order to evaluate it against 
    objectives that are not associated with a particular *system*.
    Additionally, globally relevant tasks may also feature here -- for
    example, the creation of an SKF-set of files from a definition of 
    the chemical species and a set of optimisation parameters.

Since *tasks* reflects a list of consecutive actions, it is important
to distinguish between ``pre`` and ``post`` tasks:

- ``pre``-tasks are executed before *systems* tasks
- ``post``-tasks are executed after *systems* tasks

A simple ``skopt_in.yaml`` may look like that:

.. code:: yaml

    ---
    systems:
        Si
        SiO2-quartz
        SiO2-cristobalite

    refdata:

    tasks:
        pre:
            skf
        post:
    ...        

The simplicity of this file implies a number of underlying assumptions:

* If nothing more than a ``name`` is given under ``systems`` or ``taks``,
  then SKOPT will look for ``skopt_in_name.yaml`` for a complete description.
  E.g. ``skopt_in_skf.yaml`` should be in the current directory.

* Alternatively, one specify explicit description:

  .. code:: yaml

        systems:
            Si: {file: filename_with_full_description.yaml}


.. _YAML: http://yaml.org/


