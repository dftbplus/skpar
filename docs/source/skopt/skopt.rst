.. index:: sub-packages and modules

.. _skopt:

=====================================
Subpackages and Modules
=====================================

SKOPT currently includes the following sub-packages:

    * :mod:```core`` <skopt.core>` -- the core set of modules realising the optimiser

    * :mod:```dftbutils`` <skopt.dftbutils>` -- the modules related to a DFTB model
    
Quick links to the ``core``-modules:

.. list-table::

  * - :mod:`Objectives <skopt.core.objectives>`
    - :mod:`Task Dictionary <skopt.core.taskdict>`
    - :mod:`Tasks <skopt.core.tasks>`
    - :mod:`Evaluator <skopt.core.evaluate>`
  * - :mod:`Parameters <skopt.core.parameters>`
    - :mod:`Optimiser <skopt.core.optimise>`
    - :mod:`PSO <skopt.core.pso>`
    -

Quick links to the ``dftbutils``-modules:

.. list-table::

  * - :mod:`Query DFTB <skopt.dftbutils.queryDFTB>`
    - :mod:`Qeury k-Lines <skopt.dftbutils.querykLines>`
    - :mod:`Query Bands <skopt.dftbutils.queryBands>`
  * - :mod:`Bands Analysis <skopt.dftbutils.bandstructure>`
    - :mod:`One-step Bands Calculation <skopt.dftbutils.runDFTB>`
    - :mod:`Lattice <skopt.dftbutils.lattice>`

.. seealso::

   * :ref:`tutorials`
   * :ref:`commands`


List of all modules:

.. toctree::
   :maxdepth: 2

   core/objectives
   core/tasks
   core/taskdict
   core/evaluate
   core/parameters
   core/input
   core/optimise
   core/pso
