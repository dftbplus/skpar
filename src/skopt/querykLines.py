"""
Module for k-Lines extraction and k-Label manipulation

Recall that bands contains NO information of the k-points.
So we must provide that ourselves, and reading the dftb_pin.hsd (the parsed input) seems the best way to do so.
We also need to figure out what to do with equivalent points, or points where a new path starts.
Finally, points internal to the Brilloin Zone are labeled with Greek letters,
which should be rendered properly.
"""

import logging

def getkLines(workdir='./',hsdfile='dftb_pin.hsd',DirectLattice='TET',log=logging.getLogger('__name__')):
    """
    This routine analyses the KPointsAndWeighs stanza in the (parsed) input file of DFTB+ 
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
    symmetry k-points, e.g. (see for 'Gamma' above): 
        {'X': [110], 'K': [131], 'U': [130], 'L': [0], 'Gamma': [50, 181]}
    """
    from collections import defaultdict
    from lattice import getSymPtLabel
    import sys,os

    kLines_dftb = list()

    with open(os.path.join(workdir,hsdfile)) as f:
        for line in f:
            if 'KPointsAndWeights = Klines {' in ' '.join(line.split()):
                extraline = next(f)
                while not extraline.strip().startswith("}"):
                    words = extraline.split()[:4]
                    nk,k = int(words[0]),[float(w) for w in words[1:]]
                    kLabel = getSymPtLabel(k,DirectLattice,log)
                    if kLabel:
                        kLines_dftb.append((kLabel,nk))
                    if len(words)>4 and words[4] == "}":
                        extraline = "}"
                    else:
                        extraline = next(f)
#                    except:
#                        log.critical("ERROR: Problem getting kLines from {f}. Cannot continue.".format(f=hsdfile))
#                        sys.exit(0)

    kLines = [(sp[0],sum([sp[1] for sp in kLines_dftb[:i+1]])-1) for (i,sp) in enumerate(kLines_dftb)]
    kLinesDict = defaultdict(list)
    [kLinesDict[k].append(v) for (k,v) in kLines]
    
    log.debug('Parsed {f} and obtained the follwoing\n\tkLines:{l}\n\tkLinesDict:{d}'.
            format(f=hsdfile, l=kLines, d=kLinesDict))

    # output = {'kLines': kLines, 'kLinesDict': kLinesDict}
    output = kLines,kLinesDict
    return output



def rmEquivkPts (bands, kLines, equivpts):
    """
    Given a band-structure (bands), a path in k-space (kLines) and a list of tupples 
    representing equivalent points in the Brilloin Zone (equivpts), this routine looks for
    the k-point pairs of the sort (n,n+1) and checks if they correspond to a pair of
    equivalent points. If yes, then the latter point is removed from the bands and
    the kLines, and the label of the former point is changed ot 'Lbl1|Lbl2'.
    """
    import numpy as np
    maskbands = np.ones(bands.shape[0], dtype=bool)
    maskkLines = np.ones(len(kLines),dtype=bool)
    klabels, kindexes = zip(*kLines)
    newkLines = kLines
    sortedpairedindexes = []

    for ii, pair in enumerate(equivpts):
        pairedindexes = [ (j,j+1) for j,ix in enumerate(kindexes[:-1]) 
                         if kindexes[j]+1 == kindexes[j+1] and   # two consec. indexes
                             ( pair       == klabels[j:j+2] or  # are labeled with equiv.pts
                               pair[::-1] == klabels[j:j+2] ) ] 
#        print pairedindexes
        sortedpairedindexes.extend(pairedindexes)
    sortedpairedindexes.sort(key = lambda tup : tup[0])
#    print sortedpairedindexes
    
    for jj,ix in enumerate(sortedpairedindexes):
#        print jj,ix
        newlbl = '{0}|{1}'.format(klabels[ix[0]],klabels[ix[1]])
        newkLines[ix[0]] = (newlbl,kindexes[ix[0]]-jj)
#        print newkLines[ix[1]+1:]
        newkLines[ix[1]+1:] = [(l,i-1) for l,i in newkLines[ix[1]+1:]]
#        print newkLines[ix[1]+1:]
        maskbands[kindexes[ix[1]]] = False
        maskkLines[ix[1]]=False
            
    newbands = bands[maskbands,]
    newkLines = [kpt for j,kpt in enumerate(newkLines) if maskkLines[j]] 
    
    return newbands, newkLines


def greekLabels(kLines):
    """
    Check if Gamma is within the kLines and set the label to its latex formulation.
    Note that the routine will accept either list of tupples ('label',int_index) or
    a list of strings, i.e. either kLines or only the kLinesLabels.
    Could do check for other k-points with greek lables, byond Gamma
    (i.e. points that are inside the BZ, not at the faces) but in the future.
    """
    try:
        lbls,ixs = zip(*kLines)
    except ValueError:
        lbls,ixs = kLines,None
    lbls = list(lbls)

    for i,lbl in enumerate(lbls):
        if lbl == 'Gamma':
            lbls[i] = r'$\Gamma$'
    if ixs is not None:
        result = zip(lbls,ixs)
    else:
        result = lbls
    return result



if __name__ == "__main__":
## test the rmEquivkPts routine, exhanging the order of K|U and R|M
    from queryDFTB import DFTBOutput
    from queryBands import Bands
    dftbout = DFTBOutput(workdir='./Plotter example/bulkSi',postfix='.bs')
    nElectrons = dftbout.getOutputElectrons()
    withSOC = dftbout.withSOC()
    bs_Si = Bands(workdir='./Plotter example/bulkSi',prefix='band',nElectrons=nElectrons,SOC=withSOC)
    bands,E0 = bs_Si.getBands('VBtop') 
    kLines1 = [('L', 0), ('Gamma', 108), ('X', 233), ('U', 277), ('K', 278), 
               ('K',300),('U',301), ('R',350), ('M',351),
               ('Gamma', 411),]
    newbands, newkLines = rmEquivkPts(bands,kLines1,[('K','U'),('M','R')])
    print newkLines
    print newbands.shape




