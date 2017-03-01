.. index:: install

.. _install:

====================
Install
====================

The latest release of SKOPT can be found on `Bitbucket`_.
Clone it (release-0.1 branch) and go to the newly created directory.

.. _Bitbucket: https://bitbucket.org/stanmarkov/skopt/

Assuming all dependencies are met, installation can proceed by
the conventional

.. code:: bash

        python3 setup.py install --user --record installed.info

This will try to install SKOPT in your local home directory, creating

.. code:: bash

        ~/.local/lib/python3.[?]/site-packages/skoptJ.I[.P[.S]].egg-info, 
        ~/.local/lib/python3.[?]/site-packages/skopt/. 

The executables associated with skopt will be placed in ``~/.local/bin/``,
which should be added to ``$PATH``, if not already done.

All installed files will be listed in ``installed.info``, so to uninstall 
one can do:

.. code:: bash

        cat installed.info | xargs rm -rf

Dependencies
====================
SKOPT's operation requires YAML_ support, for setting up the optimisation,
and the DEAP_ library for the Particle Swarm Optimisation engine.
If these are not available, one could install them, e.g. by:

.. code:: bash

    pip3 install deap --user
    pip3 install pyyaml --user

As with any Python application dealing with lots of calculations, 
NumPy_ is a must too.

.. _`DEAP`: http://deap.readthedocs.io/en/master
.. _`YAML`: http://pyyaml.org/wiki/PyYAMLDocumentation
.. _`NumPy`: http://www.numpy.org


Test
===================
Once installation of SKOPT and its dependencies is complete, it is
important to ensure that the test suite runs without failures, so:

.. code:: bash

    cd skopt_folder/test
    python3 -m unittest

Tests runtime is under 30 sec and should result in no errors or failures.
