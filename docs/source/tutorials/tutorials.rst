.. _tutorials:

===============
Tutorials
===============

Conceptual overview (polynomial fitting)
=============================================================
This example covers the basic structure and content of the
input file. The input file, e.g. `skopt_in.yaml`, would
typically reside in the invocation directory.
The models should have separate execution directories,
typically within the invocation folder.

The relevant files for the example are under ``skopt/test`` directory:

    * ``test_optimise.yaml``, and the folder
    * ``test_optimise/``, where the model 
    * ``test_optimise/model_poly3.py`` is executed (and located)

The example can be run in the ``skopt/test`` directory by invoking:

    * ``skopt test_optimise.yaml``,

assuming that skopt is installed.


Input YAML file
------------------------------

In this example we try to fit a 3-rd order polynomial to a curve.
Our reference data consists of points on the curve.

The setup of SKOPT consists in 4 steps:

    1. Specify the tasks necessary to evaluate the model,
    2. Declare objectives that steer the optimisation,
    3. Configure the optimisation engine (parameters, algorithm, cost-function),
    4. Translate the aliases (if used) of executables involved in model evaluation.

The corresponding yaml file, `test_optimise.yaml`_ reads:


    .. code:: yaml


        tasks:
            - set: [current.par, test_optimise, template.parameters.py ]
            - run: [mypy model_poly3.py, test_optimise ]
            - get: [get_model_data, test_optimise/model_poly3_out.dat, poly3, yval]

        objectives:
            - yval:
                doc: 3-rd order polinomial values for some values of the argument
                models: poly3
                ref: [ 36.55, 26.81875, 10., 13.43125,  64.45 ]
                eval: [rms, relerr]

        optimisation:
            algo: PSO   # particle swarm optimisation
            options:
                npart: 4   # number of particles
                ngen : 5   # number of generations
            parameters:
                - c0:  9.95    10.05
                - c1: -2.49    -2.51
                - c2:  0.499    0.501
                - c3:  0.0499   0.0501

        executables:
            mypy: 'python -v'

The reference polynomial, the reference points from it (see ``ref: [...]`` 
in the yaml file above, and the fitted 3-rd order polynomial may look as so:

.. figure:: ../../static/test_optimise_poly3.png
        :scale: 15

        Comparison of reference and fitted (gbest) polynomials, and reference data points



Optimisation of electronic parameters in DFTB
==================================================

Opitmisation of repulsive potentials for DFTB
==================================================

.. _`test_optimise.yaml`: ../../../../test/test_optimise.yaml
