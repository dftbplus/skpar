"""
Routines for reading and interpreting band-structure information from file output by DFTB+.
"""
import logging

def readBandStructure(fileBS, data, log, E0=None):
    """
    Given a file as input argument 'fileBS', the routine will read in the band-structure
    assuming the following format.
    
        1  E_1 E_2 ... E_nE
        2  E_1 E_2 ... E_nE
         ...
        nk E_1 E_2 ... E_nE
    
    __NOTA BENE:__ There is no info about the k-points!!! only their index is available.
    To derive info about the k-points automatically, one needs to parse the 
    dftb_in.hsd.bs file, looking for the K-lines stanza.
        
    __NOTA BENE:__ The routine also shifts the energy reference to the top of the valence 
    band. 

    The routine returns number of k-points, number of bands, the bands, and the index of
    the band that sets the energy reference, i.e. the index of highest VB.
    """
    import numpy as np
    import os

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
    from lattice import SymPts_k
    import sys
    from fractions import Fraction

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
    from collections import defaultdict
    import sys

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
    from calculate import Calculator
    from runtasksDFTB import RunDFTB, RunDPbands, AnalyseDFTBOut, check_var

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
    import numpy as np

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
    import numpy as np

    bands      = data['bands']
    nVBtop     = data['nVBtop']

    calcEgap = dict()

    calcEgap['Egap'] = np.min(bands[:,nVBtop+1]) - np.max(bands[:,nVBtop])

    return calcEgap

