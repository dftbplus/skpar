"""
Routines for calculating, reading and interpreting band-structure 
information, e.g. by means of dftb+, and dp_tools
"""
import os
import sys
import logging
from collections import defaultdict
import numpy as np
from math import pi, ceil
from fractions import Fraction
from skopt.lattice import SymPts_k
from skopt.calculate import Calculator
from skopt.runtasksDFTB import RunDFTB, RunDPbands, AnalyseDFTBOut, check_var


# relevant fundamental constants
Eh = 27.2114 # [eV] Hartree energy
aB = 0.52918 # [A]  Bohr radius

def readBandStructure(fileBS, data, log, E0=None):
    """
    Given a file as input argument 'fileBS', the routine will read in the band-structure
    assuming the following format.
    
        1  E_1 E_2 ... E_nE
        2  E_1 E_2 ... E_nE
         ...
        nk E_1 E_2 ... E_nE
    
    fileBS should normally be the output of `>dp_bands band.out bands`
    
    __NOTA BENE:__ There is no info about the k-points!!! only their index is available.
    To derive info about the k-points automatically, one needs to parse the 
    dftb_in.hsd.bs file, looking for the K-lines stanza.
        
    __NOTA BENE:__ The routine also shifts the energy reference to the top of the valence 
    band. 

    The routine returns number of k-points, number of bands, the bands, and the index of
    the band that sets the energy reference, i.e. the index of highest VB.
    """

    # read the bands
    log.debug("Reading bandstructure.")
    bands = np.loadtxt(fileBS,dtype=float)
    k = bands[:,0].astype(int)
    bands = np.delete(bands,0,1) # removing the kpoint-index, we are left with the Energy points only
    nk,nb = bands.shape
    log.debug("\tBandstructure consists of {0} bands sampled over {1} k-points.".format(nb,nk))

    # shift the energies to the specified reference or set the top of the valence band as a reference
    nElectrons, SOfactor = data['nElectrons'], data['SOfactor']
    nVBtop = int(nElectrons/2.*SOfactor)-1 
    if E0 is None:
        E0 = max(bands[:,nVBtop]) 
        log.debug("\tThe top of the Valence Band ({0} eV, max(band[{1}]) becomes our energy reference (0).".format(E0,nVBtop))
        bands = bands - E0
    else:
        # __NOTA BENE:__ E0, if initialised through the argument, is a key to the data dictionary
        log.debug("\t{0} = {1} eV becomes our energy reference (0).".format(E0,data[E0]))
        bands = bands  - data[E0]   
    
    # construct the output
    output = {'nkpts': nk, 'nbands': nb, 'nVBtop': nVBtop, 'bands': bands}
    return output


def getSymPtLabel(kvec, lattice, log):
    """
    This routine returns the label of a k-space symmetry point, given a tupple, representing the corresponding
    k-vector.
    __NOTA BENE:__ The symmetry points are defined as a dictionary for a given lattice type.
    This dictionary, for each lattice type, is constructed from the tables in 
    W.Setyawan and S.Curtarolo, _Comp. Mat. Sci._ __49__ (2010) pp.299-312
    see the lattice.py module for the implementation details
    """

    kLabel = None
    
    try:
        for l,klist in SymPts_k[lattice].items():
            if tuple(kvec) in klist:
                kLabel = l
    except KeyError:
        log.critical("ERROR: No symmetry point definition for the {lattice} lattice are defined.".format(lattice))
        log.critical("       Please, extend the SymPts dictionary in lattice.py module before continuing.")
        sys.exit(1)
            
    if not kLabel:
        log.debug("WARNING: Unable to match the given kvector {0} to a symmetry point of the given {1} lattice".format(kvec,lattice))
        log.debug("         Returnning fractions of reciprocal vectors as a k-point label".format(kvec,lattice))
        kx,ky,kz = Fraction(kvec[0]).limit_denominator(), Fraction(kvec[1]).limit_denominator(), Fraction(kvec[2]).limit_denominator()
        kLabel = '({0}/{1}, {2}/{3}, {4}/{5})'.format(kx.numerator, kx.denominator,
                                                      ky.numerator, ky.denominator,
                                                      kz.numerator, kz.denominator)
    return kLabel


def getkLines(hsdfile='dftb_pin.hsd',DirectLattice='FCC',log=logging.getLogger('__name__')):
    """
    This routine analyses the KPointsAndWeighs stanza in the input file of DFTB+ 
    (given as an input argument 'hsdfile', and returns the k-path, based on 
    the type of lattice (given as an input argument 'DirectLattice').
    If the file name is not provided, the routine looks in the dftb_pin.hsd, i.e.
    in the parsed file!

    The routine returns a list of tuples (kLines) and a dictionary (kLinesDict)
    with the symmetry points and indexes of the corresponding k-point in the 
    output band-structure. 

    kLines is ordered, as per the appearence of symmetry points in the hsd input, e.g.:
            [('L', 0), ('Gamma', 50), ('X', 110), ('U', 130), ('K', 131), ('Gamma', 181)]
    therefore it may contain repetitions (e.g. for 'Gamma', in this case).
    
    kLinesDict returns a dictionary of lists, so that there's a single entry for
    non-repetitive k-points, and more than one entries in the list of repetitive
    symmetry k-points, e.g. (see for 'Gamma'): 
        {'X': [110], 'K': [131], 'U': [130], 'L': [0], 'Gamma': [50, 181]}
    """

    kLines_dftb = list()

    with open(hsdfile) as f:
        for line in f:
            if 'KPointsAndWeights = Klines {' in ' '.join(line.split()):
                extraline = next(f)
                while not extraline.strip().startswith("}"):
                    try:
                        words = extraline.split()[:4]
                        nk,k = int(words[0]),[float(w) for w in words[1:]]
                        kLabel = getSymPtLabel(k,DirectLattice,log)
                        if kLabel:
                            kLines_dftb.append((kLabel,nk))
                        if len(words)>4 and words[4] == "}":
                            extraline = "}"
                        else:
                            extraline = next(f)
                    except:
                        log.critical("ERROR: Problem getting kLines from {f}. Cannot continue.".format(f=hsdfile))
                        sys.exit(0)

    kLines = [(sp[0],sum([sp[1] for sp in kLines_dftb[:i+1]])-1) for (i,sp) in enumerate(kLines_dftb)]
    kLinesDict = defaultdict(list)
    [kLinesDict[k].append(v) for (k,v) in kLines]
    
    log.debug('Parsed {f} and obtained the follwoing\n\tkLines:{l}\n\tkLinesDict:{d}'.
            format(f=hsdfile, l=kLines, d=kLinesDict))

    output = {'kLines': kLines, 'kLinesDict': kLinesDict}
    return output


def setupCalculatorsBandStructure (system,log=logging.getLogger(__name__)):
    """
    """

    calculators = []

    # Configure the SCC calculator to obtain the average SCC density within dftb
    C = Calculator(name='SCC', workdir='SCC', log=log)

    # Append the mandatory tasks to the calculator
    ## here we append instances of classes with a __call__() method
    C.append(RunDFTB('dftb_in.hsd','dftb_out.log',log=log))
    C.append(AnalyseDFTBOut(fileDetails='detailed.out',log=log))
    ## here we append a function that is implicitely transformed in an instance of a Task
    ### __NOTA BENE:__ Below, we pass C.data as a reference.
    ###                This works fine since C is an instant that would not change,
    ###                and since C.data is a list, declared upon instantiation of C
    ###                and thereafter appended to, so that the reference to C.data
    ###                does not change while its contents changes (grows).
    ###                However, if a variable _data is passed instead, then its value
    ###                will never be updated. Any subsequent updates to the value of _data
    ###                will not be seen upon the execution of the function.
    C.append(check_var, var='SCC_converged', data=C.data, value=True, critical=True, log=log)
    
    # optional tasks appended one by one 
    if hasattr(system,'plotterDOS'):
        system.plotterDOS.data = C.data
        C.append(system.plotterDOS)

    # Append the calculator to the list of calculators
    calculators.append(C)


    ## Configure the BS calculation for dftb calculation along selected k-lines
    C = Calculator(name='BS', workdir='BS', log=log)

    C.append(RunDFTB('dftb_in.hsd','dftb_out.log', chargesfile='../SCC/charges.bin', log=log))
    C.append(AnalyseDFTBOut(fileDetails='detailed.out',units='eV',log=log))

    C.append(RunDPbands(log=log))
    C.append(readBandStructure,'band_tot.dat', C.data, log=log)
    C.append(getkLines,'dftb_in.hsd', system.lattice, log=log)
    

    # optional tasks appended one by one 
    if hasattr(system,'plotterBS'):
        system.plotterBS.data = C.data 
        C.append(system.plotterBS)

    calculators.append(C)

    # return a list of the calculators
    return calculators

def analyseEelec(data, log=logging.getLogger(__name__)):
    """
    Analyse the 'Eelec' values in the data dictionary
    """

    try:
        Eelec      = data['Eh0'] + data['Escc']
    except KeyError:
        log.critical('Critical analyser error: Eh0 or Escc is not in the provided data. Cannot continue.')
        exit(1)
    return {'Eelec': Eelec}

def analyseEgap(data, log=logging.getLogger(__name__)):
    """
    Analyse the 'bands' values in the data dictionary and return the fundamental
    band-gap (Ecbmin - Evbmax).
    """

    bands      = data['bands']
    nVBtop     = data['nVBtop']

    calcEgap = dict()

    calcEgap['Egap'] = np.min(bands[:,nVBtop+1]) - np.max(bands[:,nVBtop])

    return calcEgap


def calc_masseff(band, extremum, kLineEnds, latticeconst, meff_name=None, 
                 Erange=0.008, log = logging.getLogger(__name__)):
    """
    Calculate parabolic effective mass at the specified *extremum* of a
    given *band*, calculated along two points in k-space defined by a
    list of two 3-tuples - *kLineEnds*. The direct lattice consant defining
    the length in k-space (as 2pi/*latticeconst*).

    :param band: energy values in [eV], 1D array like
    :param extremum: a function finding the extreme value in *band*, 
                     e.g. np.min()/max()
    :param kLineEnds: two 3-tuples, defining the coordinates of the 
                      endpoints of the k-line along which *band* is obtained,
                      in terms of k-scace unit vectors, e.g. if *band* 
                      is obtained along a number of points from \Gamma to
                      X, of the BZ of a cubic lattice, then kLineEnds
                      should read ((0, 0, 0), (1, 0, 0))
    :param latticeconst: length [A] of the direct lattice constant
    :param meff_name: the name to be featured in the log 
    :param Erange: Energy range [eV] over which to fit the parabola 
                   [dflt=8meV], i.e. 'depth' of the assumed parabolic well.
    :param log: logger handler; if dflt (None), then module name will feature
                as the source of the message, but logging must be configured
                elsewhere

    :return meff: the value of the parabolic effective mass [m_0]
                  at the *extremum* of the given E-kline,
                  if the extremum is not at the boundary of the given k-line.
    """
    if log is None:
        # this get's a logger, but unless logger is configured
        # somewhere, it outputs nothing
        log = logging.getLogger(__name__)
    log.debug('Fitting effective mass.')

    band = np.array(band)

    ## Scale the k-vectors in [A^{-1}], taking into account direction and lattice parameter
    a = latticeconstant # lattice constant, [A] 
    scale = 2*pi/a # first brillouin zone extends from -pi/a to +pi/a
    k1 = scale*np.array(kLineEnds[0]) # e.g. Gamma = (0,0,0)
    k2 = scale*np.array(kLineEnds[1]) # e.g. X = (1,0,0)
    klen=np.linalg.norm(k2-k1) # length of the vector from k1 to k2
    nk = len(band)   # number of k-points, implied from the number of energy points
    dk = klen/(nk-1) # distance between available k-points
    kline = dk * np.array(range(nk)) # reconstruction of kline, in units of A^{-1}

    extr = extremum(band)               # extremum value
    iextr  = np.where(band==extr)[0][0] # where along kLine it is?

    ## Special treatment is required if the point is right at the boundary, or very near it
    ## in which case we must extend the band by mirror symmetry around the extremum,
    ## before we attempt to fit
    ## Ideally, this should not happen, if we provide carefully selected paths that surround the
    ## band extrema; but this may not be possible at all to control when masses are roughly 
    ## estimated in the course of optimisation process, where it is better to minimize the 
    ## calculation of k-lines.
    if iextr == 0:
        log.debug('\tMirroring the band, since its {extr} is at {iextr}'.
                  format(extr=extremum_type,iextr=iextr))
        kline = np.concatenate((-kline[:0 :-1],kline))
        band = np.concatenate((band[:0 :-1],band))
    if iextr == nk-1:
        log.debug('\tMirroring the band, since its {extr} is at {iextr}'.
                  format(extr=extremum_type,iextr=iextr))
        band = np.concatenate((band,band[len(band)-2: :-1]))
        kline = np.concatenate((-kline[: :-1],kline[1:]))
    #log.debug(np.array(zip(kline,band)))
    #log.debug((len(band),len(kline)))
    #log.debug(np.where(band==extr)[0])
    iextr  = np.where(band==extr)[0][0]
    assert len(kline) == len(band), \
           ("Mismatch in the length of kLline {0}, and band {1}, "
            "while trying to fit effective mass")
    nk = len(kline) # if we have mirrored the band, then we have new nk

    # Select how many points to use around the extremum, in order to make the fit.
    krange = np.where(abs(band-extr)<=Erange)
    nlow = min(krange[0])
    nhigh = max(krange[0])

    log.debug(("\tFitting eff.mass on {n:3d} points around {i:3d}-th k; "
               "extremum value {v:7.3f} at {p:5.2f} of k-line").
               format(n=nhigh-nlow+1, i=iextr+1, v=extr,
                      p=kline[iextr]/kline[nk-1]*100))
    if nhigh-iextr < 3:
        log.debug('\tToo few points to the right of extremum -- Poor meff fit likely.')
        log.debug("\tConsider enlarging Erange. If it does not work, problem may "
                  "be the extremum being too close to end of k-line")
    if iextr-nlow < 3:
        log.debug("\tToo few points to the left of extremum -- Poor meff fit likely.")
        log.debug("\tConsider enlarging Erange. If it does not work, problem may "
                  "be the extremum being too close to end of k-line")
        log.debug("\tThe best solution is to resolve the k-line with more "
                  "k-points during simulation.")

    # Fit 2nd order polynomial over a few points surrounding the selected band extremum
    x = kline[nlow:nhigh+1]
    y = band[nlow:nhigh+1]
    c = np.polyfit(x,y,2)
    fit = np.poly1d(c)

    # NOTA BENE:
    # We need the c[0] coefficient when we use numpy.poly[fit|1d]

    # report the effective mass as the inverse of the curvature 
    # (i.e. inverse of the 2nd derivative, which is a const.)
    # recall that meff = (h_bar**2) / (d**2E/dk**2), in [kg]
    # meff is needed in terms of m0 a.u. - the mass of free electron at rest;
    # in a.u. h_bar is 1, m0 is 1 => we need to convert E and k in atomic units
    # our E and k are in eV and A-1, respectively and 
    # d**2E/dk**2 = 2*c[0] = const. [eV/A^-2] = const. [eV*A^2] = const/(Eh*aB^2)[a.u.]
    #m0 = 9.10938e-31 # [kg] electron rest mass
    #hbar = 1.054572e-34 # [J.s]
    #q0 = 1.602176e-19 # [C] electron charge
    #meff = (hbar*hbar)/((2*c[0])*(q0*(1.e-10)**2))/m0
    meff = 1./(2.*c[0])*(Eh*aB**2)
    log.debug("\tFitted {name:8s}: {m:8.3f}".format(name=meff_name,m=meff))
    return meff

