.. index:: about

.. _about:

==========
About
==========

SKOPT is a software tool intended to automate the optimisation of 
parameters for the Density Functional Tight Binding (DFTB) theory.
It allows a flexible and simultaneous use of diverse reference data,
e.g. from DFT calculations or experimentally obtained physical quantities.

.. figure:: ../static/skopt.diagram.png
        :width: 85%

        **Conceptual block diagram of SKOPT**.

SKOPT is implemented in `Python`_ and currently uses a Particle Swarm 
Optimisation (PSO) engine based on the `DEAP`_ library for evolutionary
algorithms. Its control is done via an input file written in YAML_.

The design of SKOPT features weak coupling between the core engine that
deals with a general multi-objective optimisation problem, and the specifics
of model execution that yields model data for a given set of parameter values.
Therefore, its extension to the closely related problems of parameter 
optimisation for empirical tight-bining (ETB) Hamiltonians or classical 
interatomic potentials for molecular dynamics should be straightforward.

.. _`Python`: http://www.python.org
.. _`DFTB+`: http://www.dftb-plus.info/
.. _Lodestar: http://yangtze.hku.hk/new/software.php
.. _dftb.org: http://www.dftb.org/home/
.. _`MIT license`: https://opensource.org/licenses/MIT
.. _`DEAP`: http://deap.readthedocs.io/en/master/
.. _`YAML`: http://pyyaml.org/wiki/PyYAMLDocumentation
