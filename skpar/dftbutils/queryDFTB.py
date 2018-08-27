import sys
import os
import logging
from os.path import abspath, expanduser, isdir
from os.path import join as joinpath
from math import pi
import numpy as np
from collections import OrderedDict
from skpar.dftbutils.lattice import Lattice, getSymPtLabel
from skpar.dftbutils.querykLines import get_klines, get_kvec_abscissa
from skpar.dftbutils.utils import get_logger

LOGGER = get_logger(__name__)

# relevant fundamental constants
Eh = 27.2114        # [eV] Hartree energy
aB = 0.52918        # [A]  Bohr radius
hbar = 1.054572e-34 # [J.s] reduced Planck's constant (h/2pi)
q0 = 1.602176e-19   # [C] electron charge
m0 = 9.10938e-31    # [kg] electron rest mass

def get_labels(ss):
    """Return two labels from a string containing "-" or two words starting with a capital.

    For example, the input string may be 'G-X', 'GX', 'Gamma-X', 'GammaX'.
    The output is always: ('G', 'X') or ('Gamma', 'X').
    """
    if '-' in list(ss):
        labels = ss.split('-')
    else:
        lss = list(ss)
        ixs = [i for i,c in enumerate(lss) if c != c.lower()]
        assert len(ixs) == 2, ixs
        assert ixs[0] == 0, ixs
        labels = [''.join(lss[:ixs[1]]), ''.join(lss[ixs[1]:])]
    return labels


# ----------------------------------------------------------------------
# Detailed Output data
# ----------------------------------------------------------------------
class DetailedOut (dict):
    """A dictionary initialised from file with the detailed output of dftb+.
    
    Useage:

        destination_dict = DetailedOut.fromfile(filename)
    """
    energy_tags = [
            ("Fermi energy:", "Ef"), # old DFTB+ 1.2
            ("Fermi level:", "Ef"),  # new DFTB+ 18.1 +
            ("Band energy:", "Eband"),
            ("TS:", "Ets"),
            ("Band free energy (E-TS):", "Ebf"),
            ("Extrapolated E(0K):", "E0K"),
            ("Energy H0:", "Eh0"),
            ("Energy SCC:", "Escc"),
            ("Energy L.S:", "Els"),
            ("Total Electronic energy:", "Eel"),
            ("Repulsive energy:", "Erep"),
            ("Total energy:", "Etot"),
            ("Total Mermin free energy:", "Emermin"), ]
    # float values, allowing for fractional number [input, output]
    nelec_tags = [
            # dftb 1.2
            ("Input/Output electrons (q):", ("nei", "neo")),
            # dftb 18.1 : "Input / Output electrons (q):"
            ("Input / Output electrons (q):", ("nei", "neo")) 
            ]
    # logical value
    conv_tags = [
            ("iSCC", ('nscc', 'scc_err')),
            ("SCC converged", True),
            ("SCC is NOT converged", True), ]

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    @classmethod
    def fromfile(cls, fp):
        fname = isinstance(fp, str)
        if fname:
            fp = open(fp, "r")
        tagvalues = {}
        with fp:
            for line in fp:
                words = line.split()
                # Energies
                for tag in cls.energy_tags:
                    if tag[0] in line:
                        # Energies are returned in [eV] (note the [-2], since 
                        # the penultimate word is the value in eV)
                        tagvalues[tag[1]] = float(words[-2])
                # Number of electrons (note this may be fractional!)
                for tag in cls.nelec_tags:
                    if tag[0] in line:
                        tagvalues[tag[1][0]] = float(words[-2])
                        tagvalues[tag[1][1]] = float(words[-1])
                # Convergence
                for tag in cls.conv_tags[1:]:
                    if tag[0] in line:
                        tagvalues[tag[0]] = tag[1]
        if fname:
            fp.close()
        # post process
        tagvalues['converged'] = 'SCC converged' in tagvalues
        tagvalues['withSOC'] = 'Els' in tagvalues
        # Remove SCC converged and SCC is NOT converged; otherwise, udpates
        # may end up with both, which will be a source of trouble.
        # Only one flag should operate: 'converged'!
        tagvalues.pop('SCC converged', None)
        tagvalues.pop('SCC is NOT converged', None)
        return cls(tagvalues)


def get_dftbp_data(implargs, database, source, model,
                   datafile='detailed.out'):
    """Get whatever data can be obtained from detailed.out of dftb+.

    Assume `source` is the directory where dftb+ was executed and that
    `datafile` is the detailed output file, along with `dftb_pin.hsd`, etc.

    Args:
        implargs(dict): implicit key-word arguments passed by caller
        database(obj): a database object that has a .update(dict) method
        source(str): directory name where dftb+ has been executed
        model(str): name of the model whose data is updated
        datafile(str): base-name of the detailed output from dftb+
    """
    logger = implargs.get('logger', LOGGER)
    workroot = implargs.get('workroot', '.')
    assert isinstance(source, str),\
        "src must be a string (directory name), but is {} instead.".\
        format(type(source))
    fin = joinpath(abspath(expanduser(workroot)), source, datafile)
    logger.debug('Getting DFTB+ data from {:s}.'.format(fin))
    data = DetailedOut.fromfile(fin)
    try:
        # assume model in database
        database.get(model).update(data)
    except (KeyError, AttributeError):
        # model not in database
        database.update({model: data})


def get_dftbp_evol(implargs, database, source, model,
                   datafile='detailed.out', *args, **kwargs):
    """Get the data from DFTB+ SCC calculation for all models.

    This is a compound task that augments the source path to include
    individual local directories for different cell volumes, based
    on the assumption that these directories are named by 3 digits.
    Similar assumption applies for the model, where the name
    of the base model is augmented by the 3-digit directory number.

    parameters:
        workroot(string): base directory where model directories are found.
        source (string): model directory
        model(str): name of the model whose data is updated
        datafile (string): optional filename holding the data.
    """
    # setup logger
    # -------------------------------------------------------------------
    logger = implargs.get('logger', LOGGER)
    workroot = implargs.get('workroot', '.')
    # In order to collect the tags that identify individual directories
    # corresponding to a given cell-volume, we must go in the base
    # directory, which includes workroot/source
    cwd = os.getcwd()
    workdir = joinpath(abspath(expanduser(workroot)), source)
    os.chdir(workdir)
    logger.info('Looking for Energy-vs-Strain data in {:s}'.format(workdir))
    # the following should be modifiable by command options
    logger.info('Assuming strain directories are named by digits only.')
    sccdirs = [dd for dd in os.listdir() if dd.isdigit()]
    # These come in a disordered way.
    # But it is pivotal that the names are sorted, so that correspondence
    # with reference data can be established!
    sccdirs.sort()
    logger.info('The following SCC directories are found:\n{}'.format(sccdirs))
    # make sure we return back
    os.chdir(cwd)
    # go over individual volume directories and obtain the data
    e_tot = []
    e_elec = []
    strain = []
    for straindir in sccdirs:
        fin = joinpath(workdir, straindir, datafile)
        logger.debug('Reading {:s}'.format(fin))
        data = DetailedOut.fromfile(fin)
        logger.debug('Done. Data: {}'.format(data))
        e_tot.append(data['Etot'])
        e_elec.append(data['Eel'])
        strain.append(float(straindir) - 100)
    # prepare to update database
    data = {}
    data['totalenergy_volume'] = e_tot
    data['elecenergy_volume'] = e_elec
    data['strain'] = strain
    # report
    logger.info('Done.')
    logger.info('\ttotalenergy_volume: {}'.format(data['totalenergy_volume']))
    logger.info('\telecenergy_volume: {}'.format(data['elecenergy_volume']))
    logger.info('\tstrain: {}'.format(data['strain']))
    outstr = ['# Total Energy[eV], Electronic Energy[eV], Volume tag']
    for total, elec, tag in zip(e_tot, e_elec, sccdirs):
        outstr.append('{:12.6g} {:10.6g} {:>10s}'.format(total, elec, tag))
    with open(joinpath(workdir, 'energy_volume.dat'), 'w') as fout:
        fout.writelines('\n'.join(outstr)+'\n')
    try:
        # assume model in database
        database.get(model).update(data)
    except (KeyError, AttributeError):
        # model not in database
        database.update({model: data})


# ----------------------------------------------------------------------
# Band structure data (including Detailed Output data)
# ----------------------------------------------------------------------
class BandsOut (dict):
    """A dictionary initialised with the bands from dp_bands or similar tool.

    Useage:

        destination_dict = BandsOut.fromfile(file)
    """
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    @classmethod
    def fromfile(cls, fp, enumeration=True):
        fname = isinstance(fp, str)
        if fname:
            fp = open(fp, "r")
        values = {}
        bands = np.loadtxt(fp, dtype=float, unpack=True)
        if enumeration:
            k = bands[0].astype(int)
            # removing the kpoint-index, we get a 2D array of energies
            #bands = np.delete(bands,0,1)
            bands = bands[1:]
        if fname:
            fp.close()
        # post process
        nb, nk = bands.shape
        values['bands'] = bands
        values['nkpts'] = nk
        values['nbands'] = nb
        return cls(values)


class Bandstructure(dict):
    """A dictionary initialised with the bands and some analysis of the bands.

    It requires two files: detailed.out from dftb+, and bands_tot.dat from dp_bands.
    It reads the bands via BandsOut; obtains the number of electrons via DetailedOut.
    It returns a dictionary with all that is in DetailedOut plus:
    'bands': energy bands (excluding k-point enumeration)
    'Ecb'  : LUMO
    'Evb'  : HOMO
    'Egap' : Ecb - Evb

    Useage:

        destination_dict = Bandstructure.fromfiles(detailed.out_file, bands_file)
    """
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    @classmethod
    def fromfiles(cls, fp1, fp2, enumeration=True):
        """Read the output of dftb+ and dp_bands and return a dictionary with band-structure data.
        """
        data = DetailedOut.fromfile(fp1)
        banddata = BandsOut.fromfile(fp2)
        data.update(banddata)
        # post process
        if data['withSOC']:
            ivbtop = int(data['neo']) - 1
        else:
            ivbtop = int(data['neo']/2.) - 1
        evb = max(data['bands'][ivbtop])
        ecb = min(data['bands'][ivbtop + 1])
        egap = ecb - evb
        data['Egap'] = egap
        data['Ecb']  = ecb
        data['Evb']  = evb
        data['ivbtop'] = ivbtop
        return cls(data)


def get_bandstructure(implargs, database, source, model,
                      detailfile='detailed.out', bandsfile='bands_tot.dat',
                      hsdfile='dftb_pin.hsd', latticeinfo=None, *args, **kwargs):
    """Get bandstructure and related data from dftb+.

    Assume that `source` is the execution directory where `detailed.out`, and
    `bands_tot.dat` can be found. Additionally, the parsed input of dftb+ --
    `dftb_pin.hsd` is also checked if lattice info is given, in order to
    analyse k-paths and provide data for subsequent plotting.
    """
    logger = implargs.get('logger', LOGGER)
    workroot = implargs.get('workroot', '.')
    assert isdir(expanduser(joinpath(workroot, source)))
    fin1 = joinpath(abspath(expanduser(workroot)), source, detailfile)
    fin2 = joinpath(abspath(expanduser(workroot)), source, bandsfile)
    fin3 = joinpath(abspath(expanduser(workroot)), source, hsdfile)
    data = Bandstructure.fromfiles(fin1, fin2)
    #
    if latticeinfo is not None:
        lattice = Lattice(latticeinfo)
        kLines, kLinesDict = get_klines(lattice, hsdfile=fin3)
        kvec, kticks, klabels = get_kvec_abscissa(lattice, kLines)
        data.update({'lattice': lattice,
                     'kLines': kLines,
                     'kLinesDict': kLinesDict,
                     'kvector': kvec,
                     'kticklabels': list(zip(kticks, klabels)),
                    })
        #logger.debug(data['lattice'])
        #logger.debug(data['kLines'])
        #logger.debug(data['kLinesDict'])
    try:
        # assume model in database
        database.get(model).update(data)
    except (KeyError, AttributeError):
        # model not in database
        database.update({model: data})

# ----------------------------------------------------------------------
# Effective masses
# ----------------------------------------------------------------------
def is_monotonic(x):
    """Return True if x is monotonic (either never increases or never decreases); False otherwise.
    """
    dx = np.diff(x)
    return np.all(dx <= 0) or np.all(dx >= 0)

def meff(band, kline):
    """Return the effective mass, in units of *m_0*, given a band a *k*-line.

    The mass is calculated as as the inverse of the curvature of *bands*,
    assuming parabolic dispersion within *kline*, working in atomic units:
    *bands* and *kline* are in Hartree and 1/Bohr, h_bar = 1, m_0 = 1

        meff = (h_bar**2) / (d**2E/dk**2), [m0]
    """
    # Fit 2nd order polynomial over the points surrounding the selected band extremum
    x = kline   # [1/Bohr]
    y = band    # [Hartree]
    c = np.polyfit(x,y,2)
    fit = np.poly1d(c)
    #logger.debug('meff band: {}'.format(y)) 
    #logger.debug('meff kline: {}'.format(x))
    #logger.debug('meff poly1d (c2, c1, c0): {}'.format(c))
    # NOTA BENE:
    # in numpy.poly[fit|1d], the 2nd order coeff is c[0]
    c2 = c[0]
    # assuming E = c2*k^2 + c1*k + c0 =>
    # dE/dk = 2*c2*k and d^2E/dk^2 = 2*c2
    return 1./(2.*c2)

def calc_masseff(bands, extrtype, kLineEnds, lattice, meff_tag=None,
                 Erange=0.008, forceErange=False, ib0=0, nb=1,
                 usebandindex=False, **kwargs):
    """A complex wrapper around meff(), with higher level interface.

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
    :param meff_name: the name to be featured in the logger 
    :param Erange: Energy range [eV] over which to fit the parabola 
                   [dflt=8meV], i.e. 'depth' of the assumed parabolic well.

    :return meff: the value of the parabolic effective mass [m_0]
                  at the *extrtype* of the given E-kline,
                  if the extremum is not at the boundary of the given k-line.
    """
    # check correct extremum type is specified
    extrdict = {'min': np.amin, 'max': np.amax}
    meffdict = {'min': 'me', 'max': 'mh'}
    logger = kwargs.get('logger', LOGGER)

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
        # this message has to go through regardless the logger is configured or not
        errmsg = ('Incorrect extremum type ({0}) for calc_masseff. '.format(extrtype),
                  '"min" or "max" supported only.')
        logger.critical(errmsg)
        sys.exit(2)

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
            "\tWill fit only the first {1} masses, as per the available bands".
            format(nb, nE))
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
        #logger.debug('Fitting effective mass {}.'.format(meff_id(ib)))
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
            logger.warning("\tCheck if extremum is at the end of k-line; "
                        "else enlarge Erange (now {0} eV) or finer resolve k-line.".format(_Erng))
        if iextr-nlow < 4 and iextr != 0:
            logger.warning("Too few points ({0}) to the left of extremum: Poor {1} fit likely.".
                        format(iextr - nlow, meff_id(ib)))
            logger.warning("\tCheck if extremum is at the end of k-line; "
                        "else enlarge Erange (now {0} eV) or finer resolve k-line.".format(_Erng))

        logger.debug("Fitting {id:8s}at{ee:7.3f} [eV], k-pos. {relpos:.2f} along nlow/nhigh {nl:>6d}/{nh:>6d}".
                format(id=meff_id(ib), relpos=extr_relpos, ee=extr, nl=nlow, nh=nhigh))

        mass = meff(band[krange]/Eh, kline[krange]*aB)  # transform to atomic units
        
        meff_data[meff_id(ib, usebandindex)] = (mass, extr, extr_relpos)
        logger.debug("Fitted  {id:8s}:{mass:8.3f} [m0], E_extr: {ee:8.3f} [eV], k_extr/klinelen: {relpos:.2f}".
                format(id=meff_id(ib, usebandindex), mass=mass, relpos=extr_relpos, ee=extr))
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

def get_effmasses(implargs, database, source, model=None, directions=None,
                  carriers='both', nb=1, Erange=0.04, usebandindex=False,
                  forceErange=False, *args, **kwargs):
    """Get effective masses along select directions for select carrier types.

    Obtain the effective masses for the given `carriers` for the first `nb`
    bands in the VB and/or CB, along the given `directions`, as well as the
    values of the extrema and their position along these `directions`.
    Label the effective masses by band index (starting from 0, within the
    band for the select carrier type), if `usebandindex` is True.
    Carrier types (`carriers`) could be 'e', 'h', 'both'.
    `Erange` is the energy range over which parabolic expansion is attempted
    """
    logger = implargs.get('logger', LOGGER)
    masses = OrderedDict()
    src_db = database.get(source)
    bands  = src_db['bands']
    nE, nk = bands.shape
    ivbtop = src_db['ivbtop']
    try:
        lattice = src_db['lattice']
#        logger.debug(lattice)
#        logger.debug('lattice is good!')
    except KeyError:
#            Since dftbp_in.hsd contains the atomic structure and cell info,
#            we may try to get the lattice type with spglib...in the future.
        logger.error('The lack of lattice information precludes interpretation'
                     ' of band-structure and effective masses.')
    kLines = src_db['kLines']
    kLinesDict = src_db['kLinesDict']
    ## suppose we have something like "L-Gamma-X|K-Gamma"
    ## this makes for two paths and three directions in total
    if directions is None:
        # derive directions from kLines, omitting segments shorter than 5 kpts
        directions = []
        for i, (lbl1, indx1) in enumerate(kLines[:-1]):
            lbl2, indx2 = kLines[i+1]
            if indx2 - indx1 > 5:
                directions.append('-'.join([lbl1, lbl2]))
    else:
        # make directions into a list of string, even if single direction given
        if not isinstance(directions, list):
            directions = [directions,]
    for direction in directions:
        logger.debug(direction)
        endpoints = get_labels(direction)
        assert len(endpoints) == 2
        logger.debug('Fitting effective mass along {}-{}.'.format(*endpoints))
        ix0 = None
        ix1 = None
        for ii, pt in enumerate(kLines[:-1]):
            # check that the labels specifying a direction form a consecutive pair
            # in kLines, and then get the corresponding indexes, sorting them too
            if kLines[ii][0] in endpoints and kLines[ii+1][0] in endpoints:
                kLineEnds = sorted([kLines[ii], kLines[ii+1]], key=lambda x: x[1])
                ix0 = kLineEnds[0][1]
                ix1 = kLineEnds[1][1]
                break
        assert ix0 is not None
        assert ix1 is not None
        kEndPts = [lattice.SymPts_k[point[0]] for point in kLineEnds]
        logger.debug(kEndPts)

        # hole masses
        # NOTABENE the reverse indexing of bands, so that mh_*_0 is the top VB
        if carriers in ['both', 'eh', True, 'h', 'holes']:
            ib0 = ivbtop
            kLine = bands[ib0:ib0-nb:-1, ix0:ix1+1]
            meff_data = calc_masseff(kLine, 'max', kEndPts, lattice,
                                     meff_tag=direction, Erange=Erange,
                                     forceErange=forceErange, nb=nb,
                                     usebandindex=usebandindex, logger=logger)
            masses.update(expand_meffdata(meff_data))
            # report also the average (arithmetic) mass
            mav = np.mean([mm[0] for mm in meff_data.values()])
            masses.update({'mh_av': mav})

        # electron masses
        # NOTABENE the direct indexing of bands, so that me_*_0 is the bottom CB
        if carriers in ['both', 'eh', True, 'e', 'electrons']:
            ib0 = ivbtop+1
            kLine = bands[ib0:ib0+nb, ix0:ix1+1]
            meff_data = calc_masseff(kLine, 'min', kEndPts, lattice,
                                     meff_tag=direction, Erange=Erange,
                                     forceErange=forceErange, nb=nb,
                                     usebandindex=usebandindex, logger=logger)
            masses.update(expand_meffdata(meff_data))
            # report also the average (arithmetic) mass
            mav = np.mean([mm[0] for mm in meff_data.values()])
            masses.update({'me_av': mav})
        #
        if model is None:
            model = source
        logger.debug('Adding the following items to model {:s}:'.format(model))
        logger.debug(masses)
        try:
            # assume model in database
            database.get(model).update(masses)
        except (KeyError, AttributeError):
            # model not in database
            database.update({model: masses})
    return masses

def plot_fitmeff(ax, xx, x0, extremum, mass, dklen=None, ix0=None, *args, **kwargs):
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
    

# ----------------------------------------------------------------------
# Eigenvalues at special points of symmetry in the BZ
# ----------------------------------------------------------------------
def get_Ek(bsdata, sympts):
    """
    """
    bands      = bsdata['bands']
    kLinesDict = bsdata['kLinesDict']
    Ek = OrderedDict()
# wrap this in try:except, and catch label not in kLinesDict
    kindexes = [kLinesDict[label][0] for label in sympts]
    for ix, label in zip(kindexes, sympts):
        Ek[label] = bands[:, ix]
    return Ek
    

def greek (label):
    """Change Greek letter names to single Latin capitals, and vice versa.

    Useful for some names of high-symmetry points inside the BZ, to shorten
    the names of Gamma, Sigma and Delta.
    Note that Lambda cannot be made into L, as it will make automatic L to 
    Lambda as well, which is wrong since L is a standard point on the BZ 
    surface.

    TODO: 
          We should handle all this shit through unicode and not bother with
          greek-to-latin mapping; just show nice greek caracters and that's 
          that. the issue is output and tests currently use mixture of
          Gamma and G extensively.
    """
    fromgreek = {"Gamma": "G", "Sigma": "S", "Delta": "D",}
    #fromgreek = {"Gamma": '\u0393', "Sigma": "\u03A3", "Delta": "\u0394", "Lambda": "\u039B"}
    togreek = dict([(v,k) for k,v in fromgreek.items()])
    try:
        lbl = fromgreek[label]
    except KeyError:
        try:
            lbl = togreek[label]
        except KeyError:
            lbl = label
    return lbl

def get_special_Ek(implargs, database, source, model=None, sympts=None,
                   extract={'cb': [0, ], 'vb': [0, ]}, align='Ef',
                   usebandindex=True, *args, **kwargs):
    """Query bandstructure data and yield the eigenvalues at k-points of high-symmetry. 
    """

    # let the user mute extraction of vb or cb by providing only the alternative key
    # this may be needed if reference energies are not available for both CB and VB
    # at the same time
    logger = implargs.get('logger', LOGGER)
    src_db = database.get(source)
    if 'cb' not in extract:
        extract.update({'cb': []})
    if 'vb' not in extract:
        extract.update({'vb': []})
    # if user does not provide sympts, then extract from kLines
    if sympts is None:
        try:
            sympts = list(src_db['kLinesDict'].keys())
        except KeyError:
            logger.critical('Attempting to guess symmetry points,'\
                            ' but kLinesDict not available.')
            sys.exit(2)
    # align the energies to a reference value, e.g. Efermi
    if isinstance(align, str):
        # that would be an energy that is computed already
        E0 = src_db[align]
    else:
        # assume a scalar
        E0 = align
    Ek = get_Ek(src_db, sympts)
    Ek = {key: val-E0 for key, val in Ek.items()}
    nVBtop     = src_db['ivbtop']
    tagged_Ek = {}
    for label in Ek:
        for bandix in extract['cb']:
            if usebandindex:
                tag = 'Ec_{:s}_{:d}'.format(greek(label), bandix)
            else:
                tag = 'Ec_{:s}'.format(greek(label))
            value = Ek[label][nVBtop + 1 + bandix]
            tagged_Ek[tag] = value
        for bandix in extract['vb']:
            if usebandindex:
                tag = 'Ev_{:s}_{:d}'.format(greek(label), bandix)
            else:
                tag = 'Ev_{:s}'.format(greek(label))
            value = Ek[label][nVBtop  - bandix]
            tagged_Ek[tag] = value
    if model is None:
        model = source
    logger.debug('Adding the following items to model {:s}:'.format(model))
    logger.debug(tagged_Ek)
    try:
        # assume model in database
        database.get(model).update(tagged_Ek)
    except (KeyError, AttributeError):
        # model not in database
        database.update({model: tagged_Ek})
    return tagged_Ek
