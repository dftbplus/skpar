.. index:: SKOPT Input File

.. _input:

======================================================================
SKOPT Input File
======================================================================

SKOPT is controlled by an input file in `YAML`_.

The input file must contain at least the following sections:

-  ``objectives``: 

- ``tasks``: 

- ``optimisation``:

Optional sections:

- ``executables``: 

A simple ``skopt_in.yaml`` may look like that:

.. code:: yaml

    ---

    tasks:
        - set: [current.par, test_optimise ]
        - run: [pythonspecial model_poly3.py, test_optimise ]
        - get: [get_model_data, test_optimise/model_poly3_out.dat, poly3, yval]

    objectives:

        - yval:
            doc: 3-rd order polinomial values for some values of the argument
            models: poly3
            ref: [ 36.55, 26.81875, 10., 13.43125,  64.45 ]


    optimisation:
        
        algo: PSO   # particle swarm optimisation
        options:
            npart: 4    # number of particles
            ngen : 5   # number of generations
        parameters:
            # either file: filename, or
            # list parameter_name: init min max type
            - c0: 9.95   10.05
            - c1: -2.49   -2.51
            - c2:  0.499    0.501
            - c3:  0.0499   0.0501

    executables:
        pythonspecial: '~/anaconda3/python'


The simplicity of this file implies a number of underlying assumptions:


.. _YAML: http://yaml.org/


