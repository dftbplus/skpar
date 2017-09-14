.. index:: tutorials

.. _tutorials:

===============
Tutorials
===============

.. _`tutorial-1`:

Tutorial 1 -- Polynomial Fitting
=============================================================
This example covers the basic structure and content of the
input file. The input file, e.g. ``skpar_optimise.yaml``, would
typically reside in the invocation directory.
The models should have separate execution directories,
typically within the invocation folder.

The relevant files for the example are under ``skpar/test`` directory:

    * ``test_optimise.yaml``, and the folder
    * ``test_optimise/``, where the model 
    * ``test_optimise/model_poly3.py`` is executed (and located)

The example can be run in the ``skpar/test`` directory by invoking:

    * ``skpar test_optimise.yaml``,

assuming that skpar is installed.


Input YAML file
------------------------------

In this example we try to fit a 3-rd order polynomial to a few points 
extracted from such a polynomial.

The setup of SKPAR consists of 4 items:

    1. A list of objectives that steer the optimisation,
    2. A list of tasks necessary to evaluate the model,
    3. An optional dictionary of aliases (used in the task list) resolving to external executables,
    4. A configuration of the optimisation engine (parameters, algorithm, cost-function).

The corresponding yaml file, `test_optimise.yaml`_ reads:


.. literalinclude:: ../../../test/test_optimise.yaml
    :linenos:
    :language: yaml

The reference polynomial, the reference points from it (see ``ref: [...]`` 
in the yaml file above, and the fitted 3-rd order polynomial may look as so:

.. figure:: ../_static/test_optimise_poly3.png
        :scale: 15

        **Comparison of reference and fitted (gbest) polynomials, and reference data points**

What is happening?
------------------------------

**Objectives:**

A model named ``poly3`` should yield data named ``yval``, to be compared 
against explicitly provided reference data ``ref: [...]``. 
Fitness evaluation of this specific objective should be based on 
root-mean-squared relative deviations, as stated after ``eval:``.

**Tasks (task-list):**

At each iteration do:

    1. Set the environment by writing the parameters to ``current.par`` and 
        substitute values in ``template.parameters.py`` to ``parameters.py``, 
        both files in ``./test_optimise`` folder. (Note that 
        ``parameters.py`` is not used by the model in this case.)
    2. Run the command ``mypy`` in the ``./test_optimise`` folder with
        input file ``model_poly3.py``. 
    3. Get the model data from ``test_optimise/model_poly3_out.dat`` and
        associate it with the ``yval`` of model ``poly3`` in the model database.

**Optimisation**

Generate four parameters (with initial range as given by a pair of
min/max values) according to particle swarm optimisation algorithm,
using 4-particle swarm, evolving it for 5 generations.

**Executables**

Whenever a run-task requires ``mypy`` command, use ``python`` instead.


.. _`tutorial-bs-exp`:

Tutorial 2 -- Optimisation of electronic parameters in DFTB
============================================================

Fitting to experimental data
--------------------------------------------------
A more elaborate example is fitting the electronic structure of bulk Si
to match a set of experimentally known *E-k* points and effective masses.

Here we set three different objectives, each of them contributing several
data items.

The corresponding ``skpar_in.yaml`` is below, with comment annotations:

.. literalinclude:: ../../../examples/Si-1/skpar_in.yaml
    :linenos:
    :language: yaml


.. _`tutorial-bs-dft`:

Fitting to DFT and experimental data
--------------------------------------------------
A yet another elaborate example is fitting the electronic structure 
of bulk Si using a combination of DFT-calculated band-structure *and*
a set of experimentally known *E-k* points and effective masses.

This is mostly as before, but provision is made to fit against 
DFT calculations not only for equilibrium volume, but also for 
slightly strained primitive cell, e.g. within +/- 2% deviation from
the equilibrium vollume.

Another important subtlety relates to the fact that the DFT-calculated
band-gap is unphysically low (~0.6 eV for Si, rather than the 
experimentally known 1.12 eV), and the objectives aim to avoid this
issue in the DFTB fit.

This is accomplished by creating a couple of separate objectives for 
fitting the shapes of the conduction and valence bands independently,
along with the objective for reaching the experimental band-gap.

The corresponding ``skpar_in.yaml`` is below, with comment annotations:

.. literalinclude:: ../../../examples/Si-2/skpar_in.yaml
    :linenos:
    :language: yaml



.. _`tutorial-3`:

Tutorial 3 -- Opitmisation of repulsive potentials in DFTB
============================================================

.. _`test_optimise.yaml`: ../../../../test/test_optimise.yaml
