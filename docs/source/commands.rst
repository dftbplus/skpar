.. highlight:: bash

.. index:: command line tools

.. _commands:

======================
Command-line utilities
======================

``skopt``
======================================================================

The ``skopt`` command is the primary tool for setting up and running 
optimisation. It can be invoked in the following scenarios.

1. Gather objectives
2. Execute model
3. Evaluate model against objectives
4. Optimise parameters against objectives

The four task reflect the following working concept.

Gather objectives
----------------------------------------------------------------------
    .. code:: bash

        skopt objectives skopt_in.yaml

Execute model
----------------------------------------------------------------------
    .. code:: bash

        skopt model skopt_in.yaml

Evaluate model against objectives
----------------------------------------------------------------------
    .. code:: bash

        skopt evaluate skopt_in.yaml

Optimise parameters against objectives
----------------------------------------------------------------------
    .. code:: bash

        skopt [optimise] skopt_in.yaml
