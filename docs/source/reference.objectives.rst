.. index:: objectives

.. _reference.objectives:

======================================================================
Objectives
======================================================================
Central to the optimisation problem are objectives. The problem is
defined as a weighted multi-objective optimisation, where each 
objective typically is associatedd with multiple data items itself. 
Each objective is scalarized, meaning that it is evaluated to a 
single scalar that represents its own cost or fitness. 
Each objective is assigned a weight, corresponding to its relative 
significance; weights are automatically normalised. 
Marler and Arora provide a good review on multi-objective
optimisation [MOO-review]_.

The declaration of an objective establishes a way for a direct 
comparison between some reference data and some model data.
With each pair of items from the reference and model data
there is associated a weight, referred to as sub-weight
that corresponds to the significance of this item relative to the 
rest of the item-pairs associated with an objective.
These sub-weights are used in the scalarisation of the objective,
and are also normalised.

Overview of Objectives Declaration
======================================================================

The declaration of an objective in the input file of SKOPT consists of
the following elements:

.. code-block:: yaml

    objectives:
        - query: # a name selected by the end-user
            doc: "Doc-string of the objective (optional)"
            models: 
                # Name of models having query_item in their database (mandatory)
            ref: 
                # Reference data or instruction on obtaining it (mandatory)
            options:
                # Options for interpretation of reference/model data (optional)
            weight: 
                # Weight of the objective (dflt: one)
            eval: 
                # How to evaluate the objective (dflt: [rms, abserr]

An example of the simplest objective declaration -- the band-gap
of bulk Si in equilibrium diamond lattice -- may look like that:

.. code-block:: yaml

    - Egap:
        doc: 'Si-diam-100: band-gap'
        models: Si.diam.100
        ref: 1.12
        weight: 5.0
        eval: [rms, relerr]

.. seealso::

   * :ref:`tutorials`

Details of Objective Declaration
======================================================================

Query Label (:code:`query`)
----------------------------------------------------------------------
:code:`query` is just a label given by the user. SKOPT does not interpret
these labels but uses them to query the model database in order to
obtain model data. Therefore, the only condition that must be met
is that the label must be available in the database(s) of the 
model(s) that are listed after :code:`models`.

It is the responsibility of the Get-Tasks to satisfy this condition.
Recall that a get-task yields certain items (key-value pairs) in the
dictionary that embodies the model database accessed as a destination 
of the task.

Certain get-tasks allow the user to define the key of the item, and
this key can be used as a query-label when declaring an objective.
Example of that is shown in :ref:`Tutorial 1 <tutorial-1>`, where
the simple :code:`get_model_data` task is used, and the query label 
is ``yval``.

Other tasks yield a fixed number of items -- examples are the 
get-tasks provided by the ``dftbutils`` package.
Please, consult their documentation to know which items are 
available as query-labels: :ref:`get-functions`.

There is one case however, in which the above significance of 
:code:`query` is disregarded, and the specified label becomes irrelevant. 
This is the case where the reference data of an objective is itself a
dictionary of key-value pairs (or results in such upon acquisition 
from a file). This case is automatically recognised by SKOPT and the 
user need not do anything special. 
The query-label in this case can be something generic.
Example of such an objective can be found in 
:ref:`Tutorial 2 <tutorial-bs-exp>`, with queries labeled as
:code:`effective_masses` or :code:`special_Ek`.


Doc-string (:code:`doc`)
----------------------------------------------------------------------
This is an optional description -- preferably very brief, which would
be used in reporting the individual fitness of the objective, and
also as a unique identifier of the objective (complementary to its
index in the list of objectives).
If not specified, SKOPT will assign the following doc-string automatically:
``doc: "model_name: query_item"``.


Model Name(s) (:code:`models`)
----------------------------------------------------------------------
This is a single name, or a list of names given by the user, and is
a mandatory field. A model name given here must be available in the
model database. For this to happen, the model must appear as a 
*destination* of a Get-Task declaration (see :ref:`get_tasks`).

Beyond a single model name and a list of model names, SKOPT supports
also a list of pairs -- [model-name, model-factor].
In such a definition, the data of each model is scaled by the 
model-factor, and a summation over all models is done, prior to 
comparison with reference data.

Therefore, the three (nonequivalent) ways in which models can be specified are:

.. code-block:: yaml

    objectives:
        - query:
            # other fields
            models: name   # or [name, ]
            # or
            models: [name1, name2, name3..., nameN]
            # or
            models:
                - [name1, factor1]
                - [name2, factor2]
                # ...
                - [nameN, factorN]


Reference Data (:code:`ref`)
----------------------------------------------------------------------
Reference data could be either explicitly provided, e.g.:
:code:`ref: [1.5, 23.4]`, or obtained from a file.
The latter gives flexibility, but is correspondingly more complicated.

Loading data from file is invoked by:

.. code-block:: yaml

    objectives:
        - query
            # other fields in the declaration
            ref:
                file: filename
                # optional
                loader_args: {key:value-pairs}
                # optional
                process:
                    # processing options

SKOPT loads data via `Numpy loadtxt() function`_, and the optional
arguments of this function could be specified by the user via
``loader_args``

.. _`Numpy loadtxt() function`: https://docs.scipy.org/doc/numpy-1.12.0/reference/generated/numpy.loadtxt.html

Typical loader-arguments are:

    * :code:`unpack: True` -- transposes the input data; 
      mandatory when loading band-structure produced from 
      ``dp_bands`` or ``vasputils``

    * :code:`dtype: {names: ['keys', 'values'], formats: ['S15', 'float']}` -- loads string-float pairs; 
      mandatory when the reference data file consists of key-value pairs per line.

The ``process`` options are interpreted only for 2D array data (ignored
otherwise), and are as follows:
    
    * :code:`rm_columns: index, list_of_indices, or, range_specification`
    * :code:`rm_rows:    index, list_of_indices, or, range_specification`
    * :code:`scale:      scale_factor`

**NOTABENE:** The indexes apply to the rows and columns of the file, and are therefore 
independent of the loader arguments (i.e. prior to potential transpose 
of the data). The indexes and index ranges are Fortran-style -- counting 
from 1, and inclusive of boundaries.

Examples:

.. code-block:: yaml

    process:
        rm_columns: 1                # filter k-point enumeration, and bands, potentially
        rm_rows   : [[18,36], [1,4]] # filter k-points if needed for some reason
        scale     : 27.21            # for unit conversion, e.g. Hartree to eV, if needed


Objective Weight: (:code:`weight`)
----------------------------------------------------------------------
This is a scalar, corresponding to the relative significance of the 
objective compared to the other objectives. Objective weights are
automatically normalised so that there sum is one.

Evaluation function : (:code:`eval`)
----------------------------------------------------------------------
Each objective is scalarised by a cost function that can be optionally
modified here. Currently only Root-Mean-Squared Deviation is supported,
but one may choose whether absolute or relative deviations are used.
The field is optional and defaults to RMS of absolute deviations.

Options : (:code:`options`)
----------------------------------------------------------------------
Options depend on the type of objective.
One common option is ``subweights``, which allows the user to specify
the relative importance of each data-item in the reference data.
These sub-weights are used in the cost-function representing the
individual objective. 

For details, see the sub-weights associated with different 
:ref:`types of objectives` below.

.. _`types of objectives`:


Objective Types
======================================================================

There are five types of objectives -- the type is deduced from the
combination of *format of the reference data* and *number of model names*.

The type of reference data could be:

    * 1-D array: e.g. the energy values of an energy-volume relation 
      of a solid

    * 2-D array: e.g. the band-structure of a solid (the set of 
      eigenstates at different *k*-number).

    * key-value pairs: e.g. named physical quantities, like effective
      masses, specific E-k points within the first Brilloin zone, etc.


1) Single reference item, single model
-----------------------------------------------------------------------------------------

    Example::
        .. code-block:: yaml

            - band_gap:
                ref: 1.12
                models: Si/bs

2) Single reference item, multiple models
-----------------------------------------------------------------------------------------

    All of the models are queried individually for the same query-item, and the result
    is scaled by the non-normalised model-weights or model factors, prior to performing
    summation over the data, to produce a single scalar.
    Reference data is a single value too.

    Example::

        .. code-block:: yaml

            - Etot:
                doc: "heat of formation, SiO2"
                models: 
                    - [SiO2-quartz/scc, 1.]
                    - [Si/scc, -0.5] 
                    - [O2/scc, -1]
                ref: 1.8 

3) Multiple reference items, multiple models
-----------------------------------------------------------------------------------------

    A single query per model is performed, over several models.

    The admitted option is ``subweights`` -- a list of floats, being normalised 
    weighting coefficients in the cost function of the objective.

    Example::
        .. code-block:: yaml

            - Etot:
                models: [Si/scc-1, Si/scc, Si/scc+1,]
                ref: [23., 10, 15.]
                options:
                    subweights: [1., 3., 1.,]

4) Key-value reference pair items, single model
-----------------------------------------------------------------------------------------

    A number of queries are made over a single model. 
    The reference is a dictionary of key-value pairs.
    The name of the objective (*meff* below) has a generic meaning, and is *not* defining 
    the query items.
    The queries are based on the keys from the reference data.
    

    The admitted option is ``subweights``, and its value must be a dictionary associating
    a weighting coefficient with a key.
    One of the subweight-keys is 'dflt', allowing to specify a weight over all keys.
    Eventually, the subweights are normalised.
    Note however, that a key is excluded from query if its sub-weight is 0.
    
    Example::
        .. code-block:: yaml

            - meff: 
                doc: Effective masses, Si
                models: Si/bs
                ref: 
                    file: ./reference_data/meff-Si.dat
                    loader_args: 
                        dtype:
                        # NOTABENE: yaml cannot read in tuples, so we must
                        #           use the dictionary formulation of dtype
                            names: ['keys', 'values']
                            formats: ['S15', 'float']
                options:
                    subweights: 
                        # consider only a couple of entries from available data
                        dflt: 0.
                        me_GX_0: 2.
                        mh_GX_0: 1.
                weight: 1.5

5) Reference Bands, single model
----------------------------------------------------------------------

**Correspondence between model data and reference data** may be non 
   trivial when the data has the character of a band-structure, i.e. 
   is 2D array. In this case correspondence can be established via 
   *use*, and *align* clauses, as in the example YAML code below.
   These clauses should be in the 'options' block of the declaration of
   an objective, as indicated.

    * `use_ref` or `use_model` (retain only enumerated bands)

      Example::
          .. code:: yaml

            options:
                use_ref: [[1, 4]]         # fortran-style index-bounds of bands to use
                use_model: [[1, 4]]
                align_ref: [4, 105]       # fortran-style index of band and k-point,
                align_model: [4, max]     # or a function (e.g. min, max) instead of k-point

    In any case, the final comparison (model vs objective) is over
    arrays of identical shape.
    Naturally, sub-weight array is of the same shape.

6. **Correspondence between sub-weights and data**, per data item, is
   established **after** the application of ``use`` and ``align`` 
   clauses from the declaration of the objective.
   When selection for applying sub-weights is based on data values,
   the values considered are with respect to the new alignment, i.e.
   after the application of the ``align`` clause.

    Bands are sets of sequences of indexed values, typically 
    representing a family of functions evaluated at a single 
    sequence of values of the argument. 
    Band-structure of solids is a typical example, hence the name.
    The representation of bands is 2D array.

    Example::
        .. code:: yaml

            - bands: 
                doc: Valence Band, Si
                models: Si/bs
                ref: 
                    file: ./reference_data/fakebands.dat # 
                    process:       # eliminate unused columns, like k-pt enumeration
                        # indexes and ranges below refer to file, not array, 
                        # i.e. independent of 'unpack' loader argument
                        rm_columns: 1                # filter k-point enumeration, and bands, potentially
                        # rm_rows   : [[18,36], [1,4]] # filter k-points if needed for some reason
                        # scale     : 1                # for unit conversion, e.g. Hartree to eV, if needed
                options:
                    use_ref: [[1, 4]]                # fortran-style index-bounds of bands to use
                    use_model: [[1, 4]]
                    align_ref: [4, max]              # fortran-style index of band and k-point,
                    align_model: [4, max]            # or a function (e.g. min, max) instead of k-point
                    subweights: 
                        # NOTABENE:
                        # --------------------------------------------------
                        # Energy values are with respect to the ALIGNEMENT.
                        # If we want to have the reference  band index as zero,
                        # we would have to do tricks with the range specification 
                        # behind the curtain, to allow both positive and negative 
                        # band indexes, e.g. [-3, 0], INCLUSIVE of either boundary.
                        # Currently this is not done, so only standard Fortran
                        # range spec is supported. Therefore, band 1 is always
                        # the lowest lying, and e.g. band 4 is the third above it.
                        # --------------------------------------------------
                        dflt: 1
                        values: # [[range], subweight] for E-k points in the given range of energy
                        # notabene: the range below is with respect to the alignment value
                            - [[-0.3, 0.], 3.0]
                        bands: # [[range], subweight] of bands indexes; fortran-style
                            - [[2, 3], 1.5]   # two valence bands below the top VB
                            - [4 , 3.5]       # emphasize the reference band
                        # not supported yet     ipoint:
                weight: 3.0


**REFERENCES**

.. [MOO-review] R.T. Marler and J.S. Arora, Struct Multidisc Optim 26, 369-395 (2004),
                "Survey of multi-objective optimization methods for engineering"


Types of objectives
======================================================================

Types of reference data
======================================================================

Queries
======================================================================

Weights and sub-weights
======================================================================



