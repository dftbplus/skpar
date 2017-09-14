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
from skpar.dftbutils.lattice import getSymPtLabel

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

        * [('L', 0), ('Γ', 50), ('X', 110), ('U', 130), ('K', 131), ('Γ', 181)]

    therefore it may contain repetitions (e.g. for 'Γ', in this case).
    
    kLinesDict returns a dictionary of lists, so that there's a single entry for
    non-repetitive k-points, and more than one entries in the list of repetitive
    symmetry k-points, e.g. (see for 'Γ' above): 

        * {'X': [110], 'K': [131], 'U': [130], 'L': [0], 'Γ': [50, 181]}
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
    Check if Γ is within the kLines and set the label to its latex formulation.
    Note that the routine will accept either list of tupples ('label',int_index) or
    a list of strings, i.e. either kLines or only the kLinesLabels.
    Could do check for other k-points with greek lables, byond Γ
    (i.e. points that are inside the BZ, not at the faces) but in the future.
    """
    try:
        lbls, ixs = list(zip(*kLines))
    except ValueError:
        lbls, ixs = kLines, None
    lbls = list(lbls)

    for i, lbl in enumerate(lbls):
        if lbl == 'Gamma':
            #lbls[i] = r'$\Gamma$'
            lbls[i] = "Γ"
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
    xt = []
    xl = []
    skipticklabel = False
    logger.debug('Constructing k-vector abscissa for BS plotting:')
    logger.debug('kLines:\n{}'.format(kLines))
    pos = 0
    xx.append(np.atleast_1d(pos))
    for item1, item2 in zip(kLines[:-1], kLines[1:]):
        l1, i1 = item1
        kp1 = lat.get_kcomp(l1)
        l2, i2 = item2
        kp2 = lat.get_kcomp(l2)
        nseg = i2 - i1
        if l1 == 'Gamma':
            l1 = 'Γ'
        if l2 == 'Gamma':
            l2 = 'Γ'
        if nseg > 1:
            seglen = np.linalg.norm(lat.get_kvec(kp2-kp1))
            xsegm, delta = np.linspace(0, seglen, nseg+1, retstep=True)
            if not skipticklabel:
                xt.append(pos)
                xl.append(l1)
            else:
                skipticklabel = False
        else:
            seglen = 0
            delta  = 0
            xsegm  = np.zeros(2)
            xt.append(pos)
            if l1 == l2:
                xl.append(l1)
            else:
                xl.append('{}|{}'.format(l1, l2))
            skipticklabel=True
        logger.debug('{:>2s} -- {:2s}: {:8.3f} -- {:8.3f} : {:8.3f}/{:<3d}={:8.3f}'.
                format(l1, l2, pos+xsegm[0], pos+xsegm[-1], seglen, len(xsegm), delta))
        xx.append(pos+xsegm[1:])
        pos += seglen
    # append the tick and label for the last point
    xt.append(pos)
    xl.append(l2)
    #
    for item in xx:
        item = np.array(item)
    xx = np.concatenate(xx)
    assert xx.shape == (kLines[-1][-1]+1,), (xx.shape, kLines)
    logger.debug('Tick labels: {}'.format(', '.join(['{}:{:.3f}'.format(l,t) for l,t in zip(xl, xt)])))
    return xx, xt, xl
