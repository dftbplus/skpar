.. index:: install

.. _install:

====================
Install
====================

The latest release of `SKOPT` can be found on `Bitbucket`_.
Download it, open the archive and go to the newly created directory.

.. _Bitbucket: https://bitbucket.org/stanmarkov/skopt/downloads

Assuming all dependencies are met, installation can proceed by
the conventional ``python3 setup.py install``.

Specifically, for local installation we recommend:

.. code:: bash

        python3 setup.py install --user --record installed.info

This will try to install `SKOPT` into your local home directory, creating

.. code:: bash

        ~/.local/lib/python?.[?]/site-packages/skoptJ.I[.P[.S]].egg-info, 
        ~/.local/lib/python?.[?]/site-packages/skopt/. 

Currently there are a few executables associated with the library,
and they would appear in ~/.local/bin/

``~/.local/bin/``, should be added to ``$PATH``, if not already done.

All installed files will be listed in ``installed.info``, so to uninstall do:

.. code:: bash

        cat installed.info | xargs rm -rf

