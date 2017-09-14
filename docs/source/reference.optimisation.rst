.. index:: optimisation

.. _`reference.optimisation`:

Optimisation
======================================================================

Optimisation is driven towards cost minimisation. The cost is evaluated 
at each iteration and new parameters are generated according to a 
prescribed algorithm.
The user could select an algorithm and set the options specific to the
algorithm in the ``optimisation:`` section of the input file.
Declaration of parameters is done in the same section too.

**Example:**

.. code-block:: yaml

    optimisation:
        algo: PSO                      # algorithm: particle swarm optimisation

        options:                       # algorithm specific
            npart: 8                   # number of particles
            ngen : 100                 # number of generations

        parameters:                    
            - Si_Ed  :  0.1 0.3        # parameter names must match with placeholders
            - Si_r_sp:  3.5 7.0        # in template files given to set-tasks above
            - Si_r_d :  3.5 8.0


Cost function
----------------------------------------------------------------------

The overall cost function is:

.. math::

    G(\{\lambda_p\}) = \sqrt{
            \left(
            \sum_j^{N}{\omega_j F_j(\{\lambda_p\})^2}
            \right)}

where :math:`\lambda_p` are the parameters, :math:`F_j()` are
the :math:`N` individual objective functions (called objectives, 
for brevity), and :math:`\omega_j` are the weights associated 
with each objective.

The scalarisation of individual objectives allows one to declare 
objectives related to different types of physical quantities and 
magnitudes, and adjust separately their contribution towards to overall
cost via the objective weights.

Weights represent the relative significance of the different objectives
towards the overall cost, and are automatically normalised:
    
.. math::

    \omega_j = \omega_j / \sum_j \omega_j

Each objective yields a scalar according to its own cost function:

.. math::

    F_j(\{\lambda_p\}) = \sqrt{
        \sum_i^M{ \omega_i \Delta_i(\{\lambda_p\})^2} }

where :math:`\Delta_i` are the deviations between model and reference
data for each of the :math:`M` data item associated with an objective 
(see :ref:`reference.objectives` for details of the declaration), 
and :math:`\omega_i` are the sub-weights associated with each data-item. 
Sub-weights are also normalised internally.

These deviations may be either absolute or relative, i.e.:
:math:`\Delta_i = m_i - r_i` or :math:`\Delta_i = (m_i - r_i)/r_i`,
with special treatment applied in the latter case where denominator vanishes.
Specifically, if both :math:`m_i` and :math:`r_i` vanish, :math:`\Delta_i = 0`,
while for a finite :math:`m_i`, :math:`\Delta_i = (m_i - r_i)/m_i`.

Optimisation Algorithm
----------------------------------------------------------------------
Currently SKPAR supports only Particle Swarm Optimisation algorithm.
The implementation follows Eq.(3) in [PSO-1]_ by J. Kennedy; 
See also the equivalent and more detailed Eqs(3-4) in [PSO-2]_.

This algorithm accepts only two options at present:

    * ``npart`` -- number of particles in the swarm
    * ``ngen``  -- number of generations through which the swarm must evolve

Each of the parameters to be optimised represents a degree of freedom
for each particle. Since parameters may have different physical units
and magnitudes, the parameters are internally normalised within the 
PSO optimiser. Upon generation of parameter values by the PSO, these
are automatically re-normalised to yield their physical significance 
upon passing to the evaluator.

See the module reference for implementation details (:ref:`pso`).

Note that the PSO is a stochastic algorithm, and it reports basic
statistics of the cost associated with each iteration.

An iteration is tagged by the pair ``(generation, particle)`` throughout
the report and log messages of the optimiser.

Parameter declaration
----------------------------------------------------------------------
From the viewpoint of an optimiser, the minimal required information 
related to parameters is their number. However, SKPAR permits a more
extensive declaration of parameters:

.. code-block:: yaml

    optimisation:
        ...
        parameters:
            - name: initial_value min_value max_value optional_type
            # or
            - name: initial_value optional_type
            # or
            - name: min_value max_value optional_type
            # or
            - name: optional type

The names of the parameters are important for using template files in
Set-Tasks (see :ref:`set_tasks`), and for reporting/logging purposes.

The default ``type`` of all parameters is float (``f``), but integer
``i`` may be supported in the future by different algorighms.

For the PSO algorithm, the initial value is ignored, so specifying
the minimal and maximal value is sufficient.

References
----------------------------------------------------------------------
.. [PSO-1] J.Kennedy, "Particle Swarm Optimization" in
    "Encyclopedia of Machine Learning" (2010), 

.. [PSO-2] 'Particle swarm optimization: an overview'. 
    Swarm Intelligence. 2007; 1: 33-57.

