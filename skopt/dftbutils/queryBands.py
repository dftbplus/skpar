"""
Routines for reading and interpreting band-structure information from file output by DFTB+.
"""
import logging
import sys
import os
import numpy as np
from collections import OrderedDict

logger = logging.getLogger(__name__)

class BandsOutput (OrderedDict):
    """
    Dictionary with the bands data
    """
    def __init__(self, initvalues=None):
        if initvalues:
            super(BandsOutput,self).__init__(initvalues)
        else:
            super(BandsOutput,self).__init__()
            
    @classmethod
    def fromfile(cls, fp, Enumeration=True):
        """
        """
        fname = isinstance(fp, str)
        if fname:
            fp = open(fp, "r")
            
        tagvalues = []
        
        logger.debug("\tReading bandstructure from {0}.".format(fp.name))
        bands = np.loadtxt(fp,dtype=float, unpack=True)
        
        if fname:
            fp.close()
            
        if Enumeration:
            k = bands[0].astype(int)
            #bands = np.delete(bands,0,1) # removing the kpoint-index, we are left with the Energy points only
            bands = bands[1:] # removing the kpoint-index, we are left with the Energy points only
            
        nb, nk = bands.shape
        logger.debug("\tBandstructure consists of {0} bands sampled over {1} k-points.".format(nb,nk))
        
        tagvalues.append(("Bands",bands))
        # these two are redundant, actually, since nk,nE = bands.shape is cheaper than writing separate queries
        tagvalues.append(("Number of energy points",nb))
        tagvalues.append(("Number of k points",nk))
        
        return cls(tagvalues)


class Bands(object):
    """
    An object encapsulating the data and methods related to the output by dp_bands.
    """
    
    def __init__ ( self, workdir='.', prefix='bands', postfix='', 
                    SeparateSpins = False, Enumeration = True, 
                    nElectrons=0, SOC=False):
        """
        Read the output file(s) from bands
        TODO: spin separation (separate spins = true)
        TODO: handle output without enumerated k-points (enumeration=false)
        NOTE: any meaningful analysis of the band-structure pivots on the knowledge of
        the number of electrons and whether the BS is calculated with
        spin-orbit coupling or not. So these are necessary input parameters.
        """
        self.logger = logger
        if SeparateSpins:
            logger.critical("Output of dp_bands cannot be handled if spin channels are separted")
            sys.exit(1)
        if not Enumeration:
            logger.warning("Enumeration=False not tested! Carefully evaluate results before moving further!")
            sys.exit(1)
            
        self.workdir = workdir
        self.datafile = os.path.join(self.workdir,prefix+"_tot.dat"+postfix)
        self.data = BandsOutput.fromfile(self.datafile, Enumeration)
        if nElectrons:
            self.indexVBtop(nElectrons,SOC)
            self.getEgap()
        
    def indexVBtop(self,nElectrons,SOC=False):
        """
        Add 'Index of top VB' to self.data. Add also a synonym 'nVBtop' which is more convenient.
        nElectrons is necessarily provided from elsewhere.
        SOC is true if spin-orbit coupling was used in the calculation producing the Bands.
        TODO: test with separated spin channels. SOfactor may need to change. The idea is
              that at this stage Bands contains both channels, independent on spin separation
              of the input bands_s1.dat and bands_s2.dat.
        """
        if SOC:
            SOfactor = 2
        else:
            SOfactor = 1
        nVBtop = int(nElectrons/2.*SOfactor)-1
        self.data.update({'Index of top VB':nVBtop})
        self.data.update({'nVBtop':nVBtop})
        return self.data['nVBtop']
        

    def getBands (self, E0=None):
        """
        Returns the band-structure, optionally aligned to the E0 energy, which
        could be a float or 'VB top'.
        """
        nVBtop = self.data['Index of top VB']
        if E0 is not None:
            if E0 == 'VB top' or E0 == 'VBtop':
                E0 = max(self.data['Bands'][nVBtop]) 
        else:
            E0 = 0
        shiftedbands = self.data['Bands'] - E0
        return shiftedbands, E0


    def getEvbtop (self):
        """
        Return the highest occupied level (HOMO)
        """
        nVBtop = self.data['nVBtop']
        return  max(self.data['Bands'][nVBtop])


    def getEgap (self):
        """
        Return the difference LUMO-HOMO, the LUMO, and the HOMO
        """
        nVBtop = self.data['nVBtop']
        nCBbot = nVBtop + 1
        Ecbbot = min(self.data['Bands'][nCBbot])
        Evbtop = max(self.data['Bands'][nVBtop])
        Egap = Ecbbot - Evbtop
        self.data['Egap'] = Egap
        self.data['Ecbbot'] = Ecbbot
        self.data['Evbtop'] = Evbtop
        return Egap, Ecbbot, Evbtop

