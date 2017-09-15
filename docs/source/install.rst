.. index:: install

.. _install:

====================
Install
====================

The latest release of SKPAR can be found on `GitHub`_.

.. _GitHub: https://github.com/smarkov/skpar/

User (w/o sudo or root privilege):

.. code:: bash

        pip3 install --upgrade --user skpar

Please omit the `--user` option above if installing within a virtual environment.
        

Developer:

Clone the repository and go to the newly created directory of the repository.

Issue the following command from the root directory of the repository.

.. code:: bash

        pip3 install --upgrade --user -e .

Please omit the `--user` option above if installing within a virtual environment.


To uninstall:

.. code:: bash

        pip3 uninstall skpar


Dependencies
====================
SKPAR's operation requires:

    * YAML_ support, for setting up the optimisation,
    * the DEAP_ library, for the Particle Swarm Optimisation engine,
    * NumPy_ for data structures, and,
    * Matplotlib_ for plotting.


.. _`DEAP`: http://deap.readthedocs.io/en/master
.. _`YAML`: http://pyyaml.org/wiki/PyYAMLDocumentation
.. _`NumPy`: http://www.numpy.org
.. _`Matplotlib`: http://matplotlib.org/


Test
===================
If cloning the repository, once installation of SKPAR and its dependencies 
is complete, it is important to ensure that the test suite runs without 
failures, so:

.. code:: bash

    cd skpar_folder/test
    python3 -m unittest

Tests runtime is under 30 sec and should result in no errors or failures.
