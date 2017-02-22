"""
Module for k-Lines extraction and k-Label manipulation

Recall that bands contains NO information of the k-points.
So we must provide that ourselves, and reading the dftb_pin.hsd (the parsed 
input) seems the best way to do so. We also need to figure out what to do 
with equivalent points, or points where a new path starts.
Finally, points internal to the Brilloin Zone are labeled with Greek letters,
which should be rendered properly.
"""
import sys
from os.path import normpath, expanduser, isdir
from os.path import join as joinpath
import logging
import numpy as np
from collections import defaultdict
from skopt.dftbutils.lattice import getSymPtLabel

logger = logging.getLogger(__name__)

def get_klines(lattice, hsdfile='dftb_pin.hsd', workdir=None, *args, **kwargs):
    """
    This routine analyses the KPointsAndWeights stanza in the input file of DFTB+ 
    (given as an input argument *hsdfile*), and returns the k-path, based on 
    the lattice object (given as an input argument *lattice*).
    If the file name is not provided, the routine looks in the default 
    dftb_pin.hsd, i.e. in the parsed file!

    The routine returns a list of tuples (kLines) and a dictionary (kLinesDict)
    with the symmetry points and indexes of the corresponding k-point in the 
    output band-structure. 

    kLines is ordered, as per the appearence of symmetry points in the hsd input, e.g.:
        [('L', 0), ('Gamma', 50), ('X', 110), ('U', 130), ('K', 131), ('Gamma', 181)]
    therefore it may contain repetitions (e.g. for 'Gamma', in this case).
    
    kLinesDict returns a dictionary of lists, so that there's a single entry for
    non-repetitive k-points, and more than one entries in the list of repetitive
    symmetry k-points, e.g. (see for 'Gamma' above): 
        {'X': [110], 'K': [131], 'U': [130], 'L': [0], 'Gamma': [50, 181]}
    """
    kLines_dftb = list()

    if workdir is not None:
        fhsd = normpath(expanduser(joinpath(workdir, hsdfile)))
    else:
        fhsd = hsdfile
    with open(fhsd, 'r') as fh:
        for line in fh:
            if 'KPointsAndWeights = Klines {'.lower() in ' '.join(line.lower().split()):
                extraline = next(fh)
                while not extraline.strip().startswith("}"):
                    # skip over commented line, in case of non-parsed .hsd file
                    while extraline.strip().startswith("#"):
                        extraline = next(fh)
                    words = extraline.split()[:4]
                    nk, k = int(words[0]), [float(w) for w in words[1:]]
                    kLabel = getSymPtLabel(k, lattice)
                    if kLabel:
                        kLines_dftb.append((kLabel, nk))
                    if len(words)>4 and words[4] == "}":
                        extraline = "}"
                    else:
                        extraline = next(fh)

    #logger.debug('Parsed {} and obtained:'.format(hsdfile))
    # At this stage, kLines_dftb contains distances between k points
    #logger.debug('\tkLines_dftb: {}'.format(kLines_dftb))
    # Next, we convert it to index, from 0 to nk-1
    kLines = [(lbl, sum([_dist for (_lbl,_dist) in kLines_dftb[:i+1]])-1) 
                        for (i,(lbl, dist)) in enumerate(kLines_dftb)]
    #logger.debug('\tkLines      : {}'.format(kLines))
    klbls = set([lbl for (lbl, nn) in kLines])
    kLinesDict = dict.fromkeys(klbls)
    for lbl, nn in kLines:
        if kLinesDict[lbl] is not None:
            kLinesDict[lbl].append(nn)
        else:
            kLinesDict[lbl] = [nn, ]
    #logger.debug('\tkLinesDict  : {}'.format(kLinesDict))
    output = kLines, kLinesDict
    return output

def greekLabels(kLines):
    """
    Check if Gamma is within the kLines and set the label to its latex formulation.
    Note that the routine will accept either list of tupples ('label',int_index) or
    a list of strings, i.e. either kLines or only the kLinesLabels.
    Could do check for other k-points with greek lables, byond Gamma
    (i.e. points that are inside the BZ, not at the faces) but in the future.
    """
    try:
        lbls, ixs = list(zip(*kLines))
    except ValueError:
        lbls, ixs = kLines, None
    lbls = list(lbls)

    for i, lbl in enumerate(lbls):
        if lbl == 'Gamma':
            lbls[i] = r'$\Gamma$'
    if ixs is not None:
        result = list(zip(lbls, ixs))
    else:
        result = lbls
    return result

def get_kvec_abscissa(lat, kLines):
    """Return abscissa values for the reciprocal lengths corresponding
    to the k-vectors derived from kLines.
    """
    xx = []
    for item1, item2 in zip(kLines[:-1], kLines[1:]):
        l1, i1 = item1
        kp1 = lat.get_kcomp(l1)
        l2, i2 = item2
        kp2 = lat.get_kcomp(l2)
        npts = i2 - i1
        if npts > 1:
            seglen = np.linalg.norm(lat.get_kvec(kp2-kp1))
            delta = seglen/npts
            xsegm = np.arange(0, seglen, delta)
        else:
            seglen = 0
            delta  = 0
            xsegm  = np.zeros(2)
        #print ('{}, {}, {}, {}, {}'.format(l1, l2, seglen/(2*pi), delta/(2*pi), xsegm/(2*pi)))
        print ('{:>5s} -- {:5s}: {:.5f} / {:.5f}'.format(l1, l2, seglen, delta))
        if xx:
            xx.append(xsegm + xx[-1][-1])
        else:
            xx.append(xsegm)
    xx = np.concatenate(xx)
    assert xx.shape == (kLines[-1][-1]+1,), xx.shape
