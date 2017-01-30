"""
Routines for calculating, reading and interpreting band-structure 
information, e.g. by means of dftb+, and dp_tools
"""
import os
import sys
import logging
from collections import OrderedDict
import numpy as np
from math import pi
from skopt.dftbutils.lattice import getSymPtLabel

logger = logging.getLogger(__name__)

# relevant fundamental constants
Eh = 27.2114        # [eV] Hartree energy
aB = 0.52918        # [A]  Bohr radius
hbar = 1.054572e-34 # [J.s] reduced Planck's constant (h/2pi)
q0 = 1.602176e-19   # [C] electron charge
m0 = 9.10938e-31    # [kg] electron rest mass


def is_monotonic(x):
    dx = np.diff(x)
    return np.all(dx <= 0) or np.all(dx >= 0)


def meff(band, kline):
    """
    Return the effective mass, in units of m0 (the electron mass at rest),
    as the inverse of the curvature of *bands*, assuming parabolic dispersion
    within *kline*, working in atomic units:
        *bands* and *kline* are in Hartree and 1/Bohr, h_bar = 1, m0 = 1

        meff = (h_bar**2) / (d**2E/dk**2), [m0]

    """
    # Fit 2nd order polynomial over the points surrounding the selected band extremum
    x = kline   # [1/Bohr]
    y = band    # [Hartree]
    c = np.polyfit(x,y,2)
    fit = np.poly1d(c)
    # NOTA BENE:
    # in numpy.poly[fit|1d], the 2nd order coeff is c[0]
    c2 = c[0]
    # assuming E = c2*k^2 + c1*k + c0 =>
    # dE/dk = 2*c2*k and d^2E/dk^2 = 2*c2
    return 1./(2.*c2)


def calc_masseff(bands, extrtype, kLineEnds, lattice, meff_tag=None, 
                 Erange=0.008, forceErange=False, ib0=0, nb=1, 
                 usebandindex=False):
    """
    Calculate parabolic effective mass at the specified *extrtype* of 
    given *bands*, calculated along two points in k-space defined by a
    list of two 3-tuples - *kLineEnds*. *lattice* is a lattice object, defining
    the metric of the kspace.

    :param bands: an array (nb, nk) energy values in [eV], or a 1D array like
    :param extrtype: type of extremum to search for: 'min' or 'max',
                     handled by np.min()/max()
    :param kLineEnds: two 3-tuples, defining the coordinates of the 
                      endpoints of the k-line along which *band* is obtained,
                      in terms of k-scace unit vectors, e.g. if *band* 
                      is obtained along a number of points from \Gamma to
                      X, of the BZ of a cubic lattice, then kLineEnds
                      should read ((0, 0, 0), (1, 0, 0))
    :param lattice: lattice object, holding mapping to kspace.
    :param meff_name: the name to be featured in the log 
    :param Erange: Energy range [eV] over which to fit the parabola 
                   [dflt=8meV], i.e. 'depth' of the assumed parabolic well.

    :return meff: the value of the parabolic effective mass [m_0]
                  at the *extrtype* of the given E-kline,
                  if the extremum is not at the boundary of the given k-line.
    """
    # check correct extremum type is specified
    extrdict = {'min': np.amin, 'max': np.amax}
    meffdict = {'min': 'me', 'max': 'mh'}

    def meff_id(ix, usebandindex=False):
        """Construct a string tag for an effective mass key.

        Change Gamma to G and eliminate '-' from meff_tag if a direction
        is recognized (e.g. something like Gamma-X becomes GX.
        Prepend type of mass (me or mh) and index if more than 1 bands
        are requested, or if *usebandindex*.
        
        Parameters:
            ix : int
                Band index.
            usebandindex : bool (False)
                Enforce band-index even if only one band requested.

        Returns:
            tag : string
                String tag for a given effective mass.
        """
        tag = meff_tag.split('-')
        try:
            tag[tag.index('Gamma')] = 'G'   # works for Gamma-X directional tags
        except ValueError:  # directional tag (e.g. A-X) but no Gamma
            pass
        tag = ''.join(tag)  # leaves a non-directional tag intact; GX otherwise
        if nb==1 and not usebandindex:
            tag = '_'.join([meffdict[extrtype], tag])
        else:
            tag = '_'.join([meffdict[extrtype], tag, '{0:n}'.format(ix)])
        return tag


    try: 
        fextr = extrdict[extrtype]
    except KeyError:
        errmsg = ('Incorrect extremum type ({0}) for calc_masseff. '.format(extrtype),
                  '"min" or "max" supported only.')
        logger.critical(errmsg)
        raise

    # check how many bands we have to deal with
    try:
        nE, nk = bands.shape   # number of bands and k-points
    except (AttributeError, ValueError): # DO NOT FORGET THE BRAKETS!
        # exception if a signle band is passed as a list or 1d array
        nE = 1                 # if bands is a list => one band only
        nk = len(bands)
        bands = np.array(bands) # we need an array from here onwards

    if nE < nb:
        logger.warning("Too many effective masses demanded ({0})."
                    "\tWill fit only the first {1} masses, as per the available bands".format(nb, nE))
        nb = nE

    beta1 = kLineEnds[0]
    beta2 = kLineEnds[1]
    k1 = lattice.get_kvec(beta1)      # get reciprocal vectors
    k2 = lattice.get_kvec(beta2)
    dk = (k2 - k1)/(nk-1)             # delta vector in direction of k1->k2
    dklen = np.linalg.norm(dk)
    klen=np.linalg.norm(k2-k1)        # length of the vector from k1 to k2
    kline = dklen * np.array(range(nk))  # reconstruction of kline, in units of A^{-1}

    meff_data = OrderedDict([])       # permits list-like extraction of data too

    for ib in range(nb):
        logger.debug('Fitting effective mass {}.'.format(meff_id(ib)))
        # set the references for the current band
        band = bands[ib0 + ib]

        # desired extremum values for each band
        extr = fextr(band)

        try:
            Erng = Erange[ib]
        except IndexError:
            Erng = Erange[0]
        except TypeError:
            Erng = Erange

        iextr  = np.where(band==extr)[0][0] # where along kLine it is?

        # find the position in k-space, and the relative position along the kline
        kextr = k1 + iextr * dk
        extr_relpos = iextr * dklen / klen
        #extr_pos_label = lattice.get_SymPtLabel(kextr)

        # Select how many points to use around the extremum, in order to make the fit.
        _Erng = 0
        krange = [0]
        while len(krange) < 5 and _Erng < max(band)-min(band):
            _Erng += Erng 
            krange = np.where(abs(band-extr)<=_Erng)[0]
        if _Erng > Erng:
            logger.warning("Erange pushed from {:.3f} to {:.3f} eV, to "\
                        "encompass {:d} E-k points including the extremum".
                        format(Erng, _Erng, len(krange)))
        # We have a problem if the band wiggles and we get an inflection point
        # within the krange -- this happens e.g. due to zone folding in Si,
        # due to its indirect band-gap.
        # So checking we are within Erng is not sufficient.
        # We have to narrow the k-range further, to guarantee that E
        # is monotonously increasing/decreasing within the krange.
        # NOTABENE: using is_monotonic as below effectively narrows the krange
        #           independently of Erange, which may lead to a far too narrow
        #           range, e.g. 1 or 2 points, especially for coarser sampling.
        #           So, where we want to NOT check for monotonic, we use the
        #           override to impose the Erange
#        logger.debug("nlow, nhigh {} {}".format(min(krange), max(krange)))
        if not forceErange:
            nlow  = min(krange)
            while not is_monotonic(band[np.where(krange<iextr)]) and iextr - nlow >= 5:
                krange = krange[1:]
                nlow = min(krange)
            nhigh = max(krange)
            while not is_monotonic(band[np.where(krange>iextr)]) and nhigh - iextr >= 5:
                krange = krange[:-1]
                nhigh = max(krange)
        nlow  = min(krange)
        nhigh = max(krange)

        if nhigh-iextr < 4 and iextr != nk-1:
            logger.warning('Too few points ({0}) to the right of extremum: Poor {1} fit likely.'.
                        format(nhigh - iextr, meff_id(ib)))
            logger.warning("Check if extremum is at the end of k-line; "
                        "else enlarge Erange (now {0} eV) or finer resolve k-line.".format(_Erng))
        if iextr-nlow < 4 and iextr != 0:
            logger.warning("Too few points ({0}) to the left of extremum: Poor {1} fit likely.".
                        format(iextr - nlow, meff_id(ib)))
            logger.warning("\tCheck if extremum is at the end of k-line; "
                        "else enlarge Erange (now {0} eV) or finer resolve k-line.".format(_Erng))

        logger.debug("Fitting {id:8s} at {ee:8.3f} [eV], {relpos:.2f}, nlow/nhigh {nl:>6d}/{nh:>6d}".
                format(id=meff_id(ib), relpos=extr_relpos, ee=extr, nl=nlow, nh=nhigh))

        mass = meff(band[krange]/Eh, kline[krange]*aB)  # transform to atomic units
        
        meff_data[meff_id(ib, usebandindex)] = (mass, extr, extr_relpos)
        logger.debug("Fitted {id:8s}:{mass:8.3f} [m0] at {ee:8.3f} [eV], {relpos:.2f}".format(
                 id=meff_id(ib, usebandindex), mass=mass, relpos=extr_relpos, ee=extr))
    return meff_data


def expand_meffdata(meff_data):
    """
    """
    expanded_data = OrderedDict()
    for k,v in meff_data.items():
        tagdict = {'me': ('cbmin', 'cbminpos'), 'mh': ('vbmax', 'vbmaxpos')}
        tagbits = k.split('_')
        masstag = k
        massval = v[0]
        extrtag = '_'.join([tagdict[tagbits[0]][0],] + tagbits[1:])
        extrval = v[1]
        kpostag = '_'.join([tagdict[tagbits[0]][1],] + tagbits[1:])
        kposval = v[2]
        expanded_data[masstag] = massval
        expanded_data[extrtag] = extrval
        expanded_data[kpostag] = kposval
    return expanded_data


def get_effmasses(bsdata, directions, carriers='both', nb=1, Erange=0.04, 
                  usebandindex=False, forceErange=False):
    """Return a dictionary with effective masses for the given *carriers* for 
    the first *nb* *bands* in the VB and CB, along the given *paths*, as well 
    as the values of the extrema and their position along the directions in 
    the *paths*.
    """
    masses = OrderedDict()
    bands      = np.transpose(bsdata['Bands'])
    nE, nk     = bands.shape
    nVBtop     = bsdata['nVBtop']
    kLines = bsdata['kLines']
    kLinesDict = bsdata['kLinesDict']
    lattice = bsdata['lattice']

    # suppose we have something like "L-Gamma-X|K-Gamma"
    # this makes for two paths and three directions in total
#    for path in paths.split('|'):
    for direction in directions:
        kLabels = direction.split('-')
        assert len(kLabels)==2
        endpoints = (kLabels[0], kLabels[1]) 
        ix0 = None
        ix1 = None
        for ii,pt in enumerate(kLines[:-1]):
            # check that the labels specifying a direction form a consequtive pair
            # in kLines, and then get the corresponding indexes, sorting them too
            if kLines[ii][0] in endpoints and kLines[ii+1][0] in endpoints:
                kLineEnds = sorted([kLines[ii], kLines[ii+1]], key=lambda x: x[1])
                ix0 = kLineEnds[0][1]
                ix1 = kLineEnds[1][1]
                break
        assert ix0 is not None
        assert ix1 is not None
        kEndPts = [lattice.SymPts_k[point[0]] for point in kLineEnds]

        # hole masses
        # NOTABENE the reverse indexing of bands, so that mh_*_0 is the top VB
        if carriers in ['both', 'eh', True, 'h', 'holes']:
            ib0 = nVBtop
            kLine = bands[ib0:ib0-nb:-1, ix0:ix1+1]
            meff_data = calc_masseff(kLine, 'max', kEndPts, lattice,
                                    meff_tag=direction, Erange=Erange,
                                    forceErange=forceErange, nb=nb,
                                    usebandindex=usebandindex)
            masses.update(expand_meffdata(meff_data))
            # report also the average (arithmetic) mass
            mav = np.mean([mm[0] for mm in meff_data.values()])
            masses.update({'mh_av': mav})

        # electron masses
        # NOTABENE the direct indexing of bands, so that me_*_0 is the bottom CB
        if carriers in ['both', 'eh', True, 'e', 'electrons']:
            ib0 = nVBtop+1
            kLine = bands[ib0:ib0+nb, ix0:ix1+1]
            meff_data = calc_masseff(kLine, 'min', kEndPts, lattice,
                                    meff_tag=direction, Erange=Erange, 
                                    forceErange=forceErange, nb=nb,
                                    usebandindex=usebandindex)
            masses.update(expand_meffdata(meff_data))
            # report also the average (arithmetic) mass
            mav = np.mean([mm[0] for mm in meff_data.values()])
            masses.update({'me_av': mav})

    return masses


def plot_fitmeff(ax, xx, x0, extremum, mass, dklen=None, ix0=None, **kwargs):
    """
    Plot the second order polynomial fitted to E(k) dispersion on top of
    *ax* axes of a matplotlib figure object.
    *mass* is the fitted effective mass
    *extremum* is extremal energy, E0
    *x0* is the relative position of the extremum along the given
    kline *xx*. 

    Assumed is that around the extremum at k0:

        E"(k) = 1/mass => E(k) = E(x) = c2*x^2 + c1*x + c0.

    Since E"(x) = 2*c2 => c2 = 1/(2*mass).
    Since E'(x) = 2*c2*x + c1, and E'(x=x0) = 0 and E(x=x0) = E0 
    => knowing E0 and x0, we can obtain c1 and c2:

        c1 = -2*c2*x0
        c0 = E0 - c2*x0^2 - c1*x0
    
    """
    c2 = 1/(2*mass/Eh/aB/aB)    # NOTABENE: scaling to eV for E and AA^-1 for k
    c1 = -2*c2*x0
    c0 = extremum - c2*x0**2 - c1*x0
    ff = np.poly1d([c2, c1, c0])
    if dklen is None:
        # xx is in Angstrom^{-1}
        yy = ff(xx)
    else:
        # xx is integer; we need dklen and ix0 to establish length
        assert ix0 is not None
        yy = ff((np.array(xx)-ix0)*dklen)
    assert len(xx) == len(yy), "len xx: {:d} != len yy {:d}".format(len(xx), len(yy))
    ax.plot(xx, yy, **kwargs)
    

def get_Eatk(bsdata, sympts):
    """
    """
    bands      = np.transpose(bsdata['Bands'])
#    nE, nk     = bands.shape
#    nVBtop     = bsdata['nVBtop']
#    kLines = bsdata['kLines']
    kLinesDict = bsdata['kLinesDict']
#    lattice = bsdata['lattice']
    Eatk = OrderedDict()
# wrap this in try:except, and catch label not in kLinesDict
    kindexes = [kLinesDict[label][0] for label in sympts]
    for ix, label in zip(kindexes, sympts):
        Eatk[label] = bands[:, ix]
    return Eatk
    

def get_tagged_Eatk(bsdata, sympts, extract={'cb': [0, ], 'vb': [0, ]}):
    """
    """
    def shorten (label):
        shortlabel = {"Gamma": "G", }
        try:
            short = shortlabel[label]
        except KeyError:
            short = label
        return short

    # let the user mute extraction of vb or cb by providing only the alternative key
    # this may be needed if reference energies are not available for both CB and VB 
    # at the same time
    if 'cb' not in extract:
        extract.update({'cb': []})
    if 'vb' not in extract:
        extract.update({'vb': []})

    Eatk = get_Eatk(bsdata, sympts)
    nVBtop     = bsdata['nVBtop']
    tagged_Eatk = OrderedDict()
    for label in Eatk.keys():
        for bandix in extract['cb']:
            tag = 'Ec_{:s}_{:d}'.format(shorten(label), bandix)
            value = Eatk[label][nVBtop + 1 + bandix]
            tagged_Eatk[tag] = value
        for bandix in extract['vb']:
            tag = 'Ev_{:s}_{:d}'.format(shorten(label), bandix)
            value = Eatk[label][nVBtop  - bandix]
            tagged_Eatk[tag] = value
    return tagged_Eatk
