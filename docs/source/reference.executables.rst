.. index:: executables

.. _`reference.executables`:

Executables
======================================================================

Executables are simple aliases to more complex commands invoking
external executables. The alias may contain command-line arguments
and options, a path to the actual command, etc.

Examples:

.. code-block:: yaml

    # define aliases to run-task commands
    executables:
        # alias an executable found along $PATH
        atom: gridatom
        # alias a shell script in ./skf/ directory
        skgen: skf/skgen.sh
        # alias a command including input arguments
        dftb: mpirun -n 4 dftb+
        # alias a command including input arguments
        bands: ~/sw/dp_tools/dp_bands band.out bands

    # use the aliases
    tasks:
        - run: [skgen, skf, skdefs.py]
        - run: [dftb,  Si/bs, out.dftb]
        - run: [bands, Si/bs, out.bands]
