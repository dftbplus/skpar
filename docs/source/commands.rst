.. highlight:: bash

.. index:: commands

.. _commands:

======================
Commands
======================

``skpar``
======================================================================

The ``skpar`` command is the primary tool for setting up and running 
optimisation. The typical usage is:

.. code:: bash

    skpar skpar_in.yaml

The few supported options could be obtained by:

.. code:: bash

    skpar -h

    usage: skpar [-h] [-v] [-n] [-e] skpar_input

    Tool for optimising Slater-Koster tables for DFTB.

    positional arguments:
    skpar_input          YAML input file: objectives, tasks, executables,
                        optimisation options.

    optional arguments:
    -h, --help           show this help message and exit
    -v, --verbose        Verbose console output (include full log as in
                        ./skpar.debug.log)
    -n, --dry_run        Do not run; Only report the setup (tasklist,
                        objectives, optimisation).
    -e, --evaluate_only  Do not optimise, but execute the task list and evaluate
                        fitness.


``dftbutils``
======================================================================

The ``dftbutils`` command can be seen as a wrapper around several 
related DFTB calculations, example being a band-structure calculation.
It works via subcommands, as follows:

.. code:: bash

    dftbutils -h

    usage: dftbutils [-h] [-v] [-n] {bands} ...

    Wrapper of DFTB+ for chaining several calculation in a single command

    optional arguments:
    -h, --help     show this help message and exit
    -v, --verbose  Verbose console output
    -n, --dry_run  Do not run; Only report the setup, i.e. tasklist.

    Available sub-commands::
    {bands}
        bands        Calculate bandstructure


``dftbutils bands``
----------------------------------------------------------------------
This commands makes the calculations of a band-structure into a single 
execution step. It assumes that the relevant calculation on a *k*-grid,
for the average density, and the following calculation along  *k*-lines
are setup in the ``scc`` and ``bs`` directories respectively.
Currently it supports `dftb+`_ as DFTB executable, and dp_bands from 
`dptools`_ as the executable that yields a band-structure array.
So what it does in the end is:

.. code:: bash

    cd workdir/scc && dftb+ & cd ../
    /bin/cp scc/charges.bin bs
    cd bs && dftb+
    dp_bands band.out bands & cd ../../

Other options may be added in the future, to eliminate the implicit 
reliance on `dftb+` and `dp_bands`.


``dftbutils set``
----------------------------------------------------------------------
This command should allow one to setup the relevant calculations for
``dftbutils bands``. Currently not supported.




.. _`dftb+`: http://www.dftb-plus.info/
.. _`dptools`: http://dftb-plus.info/tools/dptools/
