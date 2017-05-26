.. index:: config

.. _`reference.config`:

Configuration
======================================================================

Configuration of the working directory allows for a choice whether 
to execute each evaluation step in a separate subdirectory (labeled
by iteration number). Thus it permits to save each model evaluation
and is the first step towards parallelisation.

Examples:

.. code-block:: yaml

    config:
        # Template files and directories are copied to the individual
        # iteration directory under work-root; default is ``.``.
        templatedir: template

        # Workroot is the directory where each iteration dir will go
        # Default is ``.``.
        workroot: _workdir

        # All results are kept if true
        # NOTABENE: if true, then workroot may become very large!!!
        # NOTABENE: if false (DEFAULT), then plots should be written outside
        #           workroot; else will be destroyed.
        keepworkdirs: true

The complete example can be found in the `examples/C.dia`_ directory,
while the directory tree layout after the run is recorded in
`examples/C.dia/workdir.tree`_.


.. _`examples/C.dia`: ../../../examples/C.dia
.. _`examples/C.dia/workdir.tree`: ../../../examples/C.dia/workdir.tree
