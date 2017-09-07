.. index:: install

.. _install:

====================
Install
====================

The latest release of SKOPT can be found on `Bitbucket`_.

.. _Bitbucket: https://bitbucket.org/stanmarkov/skopt/


Clone the repository and go to the newly created directory of the repository.

Issue the following command from the root directory of the repository.

.. code:: bash

        pip3 install --upgrade --user -r requirements.txt -e .

Please omit the `--user` option above if installing within a virtual environment.


To uninstall:

.. code:: bash

        pip3 uninstall skopt


Dependencies
====================
SKOPT's operation requires:

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
Once installation of SKOPT and its dependencies is complete, it is
important to ensure that the test suite runs without failures, so:

.. code:: bash

    cd skopt_folder/test
    python3 -m unittest

Tests runtime is under 30 sec and should result in no errors or failures.
