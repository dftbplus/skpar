.. index:: Reference Data

.. _reference_data:

======================================================================
Reference Data
======================================================================

Types of Reference Data
======================================================================

There are different ways to classify the types of reference data used
in optimisation. Two classifications are pertinent to the context of
SKF optimisation:

    * system-specific: pertaining to a given atomic system, 
      e.g. the band-structure of alpha-quartz SiO2;

    * global: relating different atomic systems, e.g. the difference
      in total energies between alpha-quartz and beta-cristobalite
      SiO2.

Below, we discuss the former type first.

System-specific Reference Data
----------------------------------------------------------------------

Complete band structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This would typically come from DFT calculations. Assuming N bands and 
M k-points, the file storing the full BS will have M lines with N or 
N+1 columns, depending on whether kpoint-index is included or not:

.. code:: bash

    kpt_index E(band1) E(band2) E(band3) .... E(bandN)

These would typically be imported by:

.. code:: python

    bands = np.loadtxt("bands_tot.dat", unpack=True)[1:,]

which will eliminate the band-index, and allow accessing
individual bands by, e.g. -- for spin degenerate system:

.. code:: python

    topvb = bands[nelectrons-1]

Band-gaps, E-k point of special symmetry, k-space position of extrema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This may be known from experiment: e.g., fundamental indirect band-gap
or the direct band-gap at Gamma point. Associated with these values 
may be position of the extrema points in k-space. These would
typically be specified as key-value pairs.

.. code:: yaml

    band_gaps:
        -E_gap         : 1.12  # eV, fundamental

    special_Ek_points:
        -E_gap         : 1.12  # eV
        -E_X           : 1.12  # eV

    extremal_positions:
        -pos_min_GX    : 0.85  # fraction of Gamma-X line
        -pos_min_GL    : 1.0   # fraction of Gamma-L line
    
The challenge here is two-fold:

  * Notation must be standardised, or mapping must be allowed
  * Interpretation is required of the lattice type, in order
    to derive significance from labels refering to Delta, X etc.

Effective masses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
These would be typically from experiment or an accurate calculation, 
probably from a publication, and would be in a file with the original 
crystallographic notation:

.. code:: yaml

    effective_masses:
        -me_Xl         : 0.92  # [m_0], longitudinal along Gamma-X
        -me_Xt         : 0.19  # [m_0], transverse along Gamma-X
        -m_so          : 0.23  # [m_0], spin orbit, holes, isotropic
        -m_hh_111      : 1.10  # [m_0], heavy holes along 111
        -m_lh_110      : 0.35  # [m_0], light holes along 110

But we would like to re-map the names:

.. code:: yaml

    map_effective_masses:
        -me_GX   : me_Xl
        -mh_GK_0 : m_lh_110
        -mh_GL_2 : m_hh_111
        -mh_GL_4 : m_so
        -mh_GK_4 : m_so
        -mh_GX_4 : m_so

Note also that ``me_Xt`` is very hard to deal with, because *a priori*
we do not know where the minimum along Gamma-X would be, and therefore
do not know the k-vectors for expanding the band-structure with fine
detail. So for the moment, we may want to not deal with it.
It should be possible to automate, but requires a new dftb_in.hsd to
be constructed on the fly, once we know where the band minimum is.

Again, as in the case with special symmetry points, we need to 
understand the lattice, and have some convention, in order to make
sense of the above. Mapping helps with the convention:

    * :code:`me\_\*` : electron mass
    * :code:`mh\_\*` : hole mass
    * :code:`\*_GX_\*`  : Gamma-X direction; similar for other points
    * :code:`me_GX_0`: electron mass of the lowest conduction band
    * :code:`mh_GX_0`: hole mass of the highest valence band
    * :code:`mh_GX_0/2/4`: hole mass of the heavy, light, spin-orbit mass
                   typically

Energy-volume curves
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Energy-volume curve would typically be the result of a fit from the 
equation of state, after parsing the total energies of a DFT calculation.
We assume two column data: column 1: Volume, column 2: Energy, both in
atomic units.
Standard import then yields the data:

.. code:: python

    volen = np.loadtxt('volen.dat')

Each reference item will be obtained by first index; 
no need to transpose, hence :code:`unpack=False` (default).

Global Reference Data
----------------------------------------------------------------------
An example is the total electronic energy *versus* lattice structure,
e.g. for a set of crystalline atomic systems of a given chemical 
composition, e.g. the various polymorphs of silica.
The format of such reference data will be similar to the energy-volume
curves.

Cost function
======================================================================

Optimisation is driven towards cost minimisation. Associated with each 
reference item (:math:`i`), there must be a *weight* (:math:`$\omega_i$`),
so that the deviations of the current model from the target are 
weighted by the relative significance of each target, when the 
performance of the model is evaluated.

We intend an optimisation over several different systems, and further
to the classification introduced in the previous section, it is 
advantageous to introduce some hierarchy of the reference data and the
associated weights. This will help to compose the final expression of
the cost function.

An important thing to note by inspecting the *types* of reference data
above is the fact that reference items can have different units, and 
vastly different magnitudes! For example, effective masses 
(:math:`[m_0]`), band-energies (a few :math:`[eV]`), extrema positions
(unitless fractions of k-lengths), total energies (hundreds of :math:`[eV]`).
This must be taken into account in constructing the cost function,
by some sort of normalisation, or by resorting to the use of relative
deviations.

Cost Function Expression
----------------------------------------------------------------------
One possibility is to use two-level hierarchy, based on the division of
global and system-specific reference items.
This assumes that the reference items within each system are flattened
out, and have corresponding weights :math:`\omega_s`, while the 
relative weight of each system is treated on par with the global 
reference items, and accordingly associated with a global weight 
:math:`\omega_g`.

For such a division, an expression for the weighted 
*root mean squared relative deviation* is:

.. math::

    f(\{\lambda_i\}) = \sqrt{
        \sum_g{ \omega_g \left(
            \sum_s{\omega_s \delta_s(\{\lambda_i\})^2}
            +
            \sum_\gamma{\delta_\gamma(\{\lambda_i\})^2}
            \right)}}

In this equation, :math:`\{\lambda_i\}` is the parameter set,
:math:`\omega_{g,s}` are the *global* and *system-specific* weights,
and :math:`\delta` is the *relative error*.

It may be convenient however, to have further splitting according to
the system specific types of reference data. In this way, one could
specify more easily e.g. the relative importance of *E-k* points
with respect to effective masses or position of band extrema.
The modified expression in this case would be:

.. math::

    f(\{\lambda_i\}) = \sqrt{
        \sum_g{ \omega_g \left(
            \sum_s{\omega_s 
                \sum_\sigma{ \omega_\sigma \delta_\sigma(\{\lambda_i\})^2} }
            +
            \sum_\gamma{\delta_\gamma(\{\lambda_i\})^2}
            \right)}}

Here, the subscript :math:`_s` enumerates the *types* of *system-specific*
reference data, whereas the subscript :math:`_\sigma` enumerates the actual
reference *items* of a given type.

Then, one is entitled to ask: *Where do we stop* with this nesting?
It is conceivable for example to give different weights to different bands
inside a full reference band-structure, and further give different weights
to different k-points within a band.

**Important Note 1**

Weights sharing the *same subscript* are normalised so that their sum 
yields 1. For example, if user weights are :math:`\omega_s\prime`, then:
    
.. math::

    \omega_s = \omega_s\prime / \sum_s \omega_s\prime

**Important Note 2**

The hierarchy can be easily flattened by virtue of associativity.
However, it gives some convenience for the user.

**Example**

Let's take two atomic systems with different lattice. Assume we deal
with electronic structure only, and we want to have certain difference
in total electronic energy (no repulsive) as a third global parameter.
So we have three global weights.
Lets treat the two systems the same, with weights of 
:math:`\omega_{1,2}\prime=1`.
The third global reference is not so crucial to meet -- let's give it
5 times lower value: :math:`\omega_3\prime=0.2`.
After normalisation, we have 
:math:`\omega_{1,2}=0.454` and :math:`\omega_3=0.091`.
Suppose now we care about the band structure, but most of all, about
the highest VB and lowest CB, and to a smaller extent, for several 
effective masses. *How to convey that?*

