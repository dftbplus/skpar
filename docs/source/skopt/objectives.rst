.. index:: Opitmisation objectives

.. _objectives:

======================================================================
Objectives
======================================================================

Central to the optimisation problem are objectives. The problem is
defined as a weighted multi-objective optimisation, where each objective 
typically is composed of multiple sub-objectives itself, but upon
evaluation, its fitness is a single scalar. Each objective is assigned
a weight, corresponding to its relative significance.
A good review of the mathematical formulation is found here [MOO-review]_.

The declaration of an objective establishes a way for a direct 
comparison between some reference data and some model data.
With each data item is associated a weight, corresponding to
the significance of this item relative to the rest of the items.
These weights are regarded as sub-weights, and are used for 
the scalarisation of a given objective.


Assumptions
======================================================================

1) **Objective name** defines the object to be queried from the Model 
   Database (MDB). Exception to this rule is an objective with 
   key-value pairs as reference data -- the keys define the queries 
   in that case, and the name of the objective is irrelevant.

2) **Format of reference data** in combination with the **number of model
   names** uniquely defines the type of objective. 
   The type of reference data could be:

    * 1-D array: e.g. energy-volume relation of a solid

    * 2-D array: e.g. band-structure of a solid

    * key-value pairs: e.g. named physical quantities, like effective
      masses, E-k points within the first Brilloin zone, etc.


3) **Correspondence between model data and reference data** may be non 
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

   A *filter* clause may be added in the future.:

    * 'filter' (remove enumerated entries)

      Example::
          .. code:: yaml

            filter:
                columns: 1                # e.g. filter k-point enumeration, and bands, potentially
                rows   : [18,36], [1,4]   # filter k-points if needed for some reason
 

    In any case, the final comparison (model vs objective) is over
    arrays of identical shape.
    Naturally, sub-weight array is of the same shape.

5) **Correspondence between sub-weights and data**, per data item, is
   established **after** the application of ``use`` and ``align`` 
   clauses from the declaration of the objective.
   When selection for applying sub-weights is based on data values,
   the values considered are with respect to the new alignment, i.e.
   after the application of the ``align`` clause.

6) **Index counting** starts from 1, and index ranges are inclusive of
   both boundaries, i.e. FORTRAN-style is used.


Objective Types
======================================================================

**1) Single reference value, single model (underlying class: `ObjValues`)** 
-----------------------------------------------------------------------------------------

    Example::
        .. code:: yaml

            objectives:
                - band_gap:
                    doc: "Band gap of Si (diamond)"
                    models: Si/bs
                    ref: 1.12
                    weight: 3.0

**2) Single reference value, multiple models (underlying class: `ObjWeightedSum`)**
-----------------------------------------------------------------------------------------

    There are multiple models, each weighted individually and queried
    for a single-valued item. Reference data is a single value.

    Example::
        .. code:: yaml

            - Etot:
                doc: "heat of formation, SiO2"
                models: 
                    - [SiO2-quartz/scc, 1.]
                    - [Si/scc, -0.5] 
                    - [O2/scc, -1]
                ref: 1.8 
                weight: 1.2

**3) Multiple reference values, multiple models (underlying class: `ObjValues`)**
-----------------------------------------------------------------------------------------

    A single query per model is performed, over several models.

    Example::
        .. code:: yaml

            - Etot:
                models: [Si/scc-1, Si/scc, Si/scc+1,]
                ref: [23., 10, 15.]
                options:
                    subweights: [1., 3., 1.,]

**4) Key-value reference pairs, single model (underlying class: `ObjKeyValuePairs`)**
-----------------------------------------------------------------------------------------

    A number of queries are made over a single model. 
    The reference is a dictionary of key-value pairs.
    The name of the objective (*meff* below) has a non-deterministic 
    meaning, since the queries are based on the keys from the reference data.
    Actually, only a subset of queries are performed, based on the 
    reference items with non-zero sub-weights -- see below.
    
    Example::
        .. code:: yaml

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

**5) Reference Bands, single model (underlying class: `ObjBands`)**
----------------------------------------------------------------------

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


Details of the ``objectives`` module
======================================================================

.. automodule:: skopt.objectives
    :members:
