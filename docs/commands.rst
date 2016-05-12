.. highlight:: bash

.. index:: command line tools

.. _commands:

======================
Command-line utilities
======================

SKOPT
======================================================================

The `skopt` command is the primary tool for setting up and running 
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

Evaluate model against objecctives
----------------------------------------------------------------------
    .. code:: bash

        skopt evaluate skopt_in.yaml

Optimise parameters against objectives
----------------------------------------------------------------------
    .. code:: bash

        skopt optimise [optimisation options] skopt_in.yaml


usage: skopt [-h] [-np NP] [-ng NG] [-etol ETOL] [--evaluate-only] skopt_input

Tool for optimising Slater-Koster tables for DFTB.

positional arguments:
  skopt_input           Input to skopt: description of systems, targets, weights, etc.

optional arguments:
  -h, --help            show this help message and exit
  -np NP, -npart NP, -nind NP
                        Number of individuals(particles) in the population(swarm).
  -ng NG, -ngen NG      Number of generations through which the population(swarm) evolves.
  -etol ETOL            Maximum tolerable error [%], below which optimisation stops.
  --evaluate-only       Do not perform optimisation. Instead, only evaluate a given SKF set against reference data.
