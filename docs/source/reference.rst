.. index:: reference

.. _about:

========================================
Input File Reference
========================================

SKOPT is controlled by an input file in `YAML`_. The filename is given as 
an argument to the ``skopt`` command (e.g. ``skopt skopt_in.yaml``).
Examples of input files can be seen in :ref:`tutorials`, while here we
provide the full details.

.. _`YAML`: http://pyyaml.org/wiki/PyYAMLDocumentation

The input file must contain the following four sections, which are
covered in this reference. The sections of the reference correspond to 
sections in the input file.


.. code-block:: yaml

    tasks:
        # tasks defining the model
    
    objectives:
        # objectives steering the optimisation

    optimisation:
        # optimisation strategy

    # optional
    executables:
        # alises of executable commands used in tasks


.. toctree::

    reference.tasks
    reference.objectives
    reference.optimisation
    reference.executables
