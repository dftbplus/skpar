import os, logging
from collections import OrderedDict

class DetailedOutput (OrderedDict):
    
    energytags = ["Fermi energy", "Band energy", "TS", "Band free energy", 
                  "Energy H0", "Energy SCC", "Energy L.S", "Total Electronic energy",
                  "Repulsive energy", "Total energy", "Total Mermin free energy"]
    
    def __init__(self, initvalues=None):
        if initvalues:
            super(DetailedOutput,self).__init__(initvalues)
        else:
            super(DetailedOutput,self).__init__()
    
    @classmethod
    def fromfile(cls, fp):
        fname = isinstance(fp, str)
        if fname:
            fp = open(fp, "r")
        tagvalues = []
        # parse the file for the values of interest
        # since the file is very big, we should parse it in reverse, but I don't know how
        # (note that the lines of greatest interest are at the end)
        with fp:
            for line in fp:
                words = line.split()
                # Energies
                for etag in cls.energytags:
                    if etag in line:
                        # Energies are returned in [eV] (note the [-2], since 
                        # the penultimate word is the value in eV)
                        tagvalues.append((etag,float(words[-2])))
                # Number of electrons (note this may be fractional!)
                if 'Input/Output electrons (q):' in line:
                    tagvalues.append(('Input electrons',float(words[-2])))
                    tagvalues.append(('Output electrons',float(words[-1])))
                if 'Neutral charge' in line:
                    tagvalues.append(('Neutral charge',float(words[-1])))
                if 'Input/Output charge' in line:
                    tagvalues.append(('Input charge',float(words[-2])))
                    tagvalues.append(('Output charge',float(words[-1])))
                # Convergence
                if 'SCC converged' in line:
                    tagvalues.append(('SCC converged',True))
                if 'SCC is NOT converged' in line:
                    tagvalues.append(('SCC converged',False))
                # Current [A]
                if 'Total Current' in line:
                    # the key becomes "TotalCurrent(1-2)" or whatever the contact indexes
                    tagvalues.append(("".join(words[:-2])[:-1],float(words[-2])))
                    
        if fname:
            fp.close()
        # post process
        if 'Energy L.S' in dict(tagvalues):
            tagvalues.append(('Spin orbit coupling',True))
        else:
            tagvalues.append(('Spin orbit coupling',False))
        return cls(tagvalues)


class DFTBOutput(object):
    
    def __init__(self, workdir='.', postfix=''):
        self.workdir = workdir
        fp = open(os.path.join(self.workdir, "detailed.out"+postfix,), "r")
        self.data = DetailedOutput.fromfile(fp)
        fp.close()

    def getEnergy (self, etag):
	try:
	    energy = self.data[etag]
	except:
	    energy = None
	return energy
    
    def getOutputElectrons (self):
        try:
            chrg = self.data['Output electrons']
        except:
            try:
                chrg = self.data['Output charge']
            except:
                chrg = None
        return chrg
    
    def getOutputCharge (self):
        return self.getOutputElectrons()
    
    def getInputElectrons (self):
        try:
            chrg = self.data['Input electrons']
        except:
            try:
                chrg = self.data['Input charge']
            except:
                chrg = None
        return chrg
    
    def getInputCharge (self):
        return self.getInputElectrons()
    
    def getNeutralCharge (self):
        try:
            chrg = self.data['Neutral charge']
        except:
            chrg = None
        return chrg
    
    def getCurrent (self,contacts=(1,2)):
        c1 = contacts[0]
        c2 = contacts[1]
        try: 
            current = self.data["TotalCurrent({0}-{1})".format(c1,c2)]
        except:
            current = None
        return current
    
    def sccConverged (self):
        return self.data['SCC converged']
    
    def withSOC (self):
        return self.data['Spin orbit coupling']



class QueryDataDFTB (object):
    """
    This class encapsulates all steps of collecting the information from 
    the DFTB+ runs to calculate the band-structure and putting the 
    information in the 'data' dictionary that is passed as argument upon
    initialisation. The arguments are:
    data     - obligatory dictionary, possibly containing 'lattice' and 
               'equivkpts' fields, if we want to get 'bandsPlt' and 'kLinesPlt'
    workdir  - work directory, where detailed.out, dftb_pin.hsd and 
               bands_tot.dat must be.
    getBands - logical, if true, an attempt to query bands_tot.dat will be made
    getHOMO  - logical, if true, Evbtop, Egap and Ecbtop will be extracted
    Eref     - reference energy for the band-structure; 'bands' will be shifted
               according to Eref, unless it is None. 
               Valid values are None, 'VBtop', or a float.
    getkLines - analyse dftb_pin.hsd and return kLines and kLinesDict in data
    prepareforplot - logical, if true, 'bandsPlt' and 'kLinesPlt' will be 
               obtained; but a prerequisite is 'lattice' type, so that kLines 
               may be queryied. If 'equivkpts' (a list of tupples) is in data, 
               then attempt will be made to eliminate the duplicate.
    log      - logger for runtime messages
    """
    
    def __init__(self, data, workdir='.', 
	         postfix='', bandsprefix='bands',
                 getBands=True, Eref=None, getHOMO=True, getkLines=True,
		 prepareforplot=True, log=logging.getLogger('__name__')):
        self.workdir = workdir
	self.postfix = postfix
	self.bandsprefix = bandsprefix
        self.data = data
        self.getBands = getBands
        self.Eref = Eref
        self.getHOMO = getHOMO
	self.getkLines = getkLines
        self.prepareforplot = prepareforplot
        self.log = log
        
    def query(self):
        """
        """
#        from skopt.queryDFTB import DFTBOutput
        from queryBands import Bands
        from querykLines import getkLines, rmEquivkPts, greekLabels
        # get data from detailed.out of dftb+
	self.log.debug("Parsing dftb output from {0}".format(self.workdir))
        dftbout = DFTBOutput(self.workdir)
        for key,value in dftbout.data.iteritems():
            self.data[key] = value
        
        # attempt to obtain the band structure
        if self.getBands:
            if self.getHOMO:
                nElectrons = dftbout.getOutputElectrons() # alt: self.data['Output electrons']
                withSOC = dftbout.withSOC()               # alt: self.data['Spin orbit couplint']
            else:
                nElectrons = 0
                withSOC = False

	    self.log.debug("...obtained nElectrons={0}".format(nElectrons))
	    self.log.debug("...obtained withSOC={0}".format(withSOC))

            try:
                bs = Bands(workdir=self.workdir, prefix=self.bandsprefix, postfix=self.postfix,
			    nElectrons=nElectrons, SOC=withSOC,)
            except:
                self.log.critical('\tCould not parse the bandstructure file.'
                                  '\tCheck bands_tot.dat exists in {0}'.format(self.workdir))
                sys.exit([1])
            # if we pass the try statement, then we have the bs object
	    self.log.debug("...acquired the following items:\n{0}".format(bs.data.keys()))
            for key,value in bs.data.iteritems():
                self.data[key] = value

	    if self.Eref is not None:
		self.data['Bands'] = bs.getBands(self.Eref)[0]
                
            # now prepare data for analysis and plotting. here we need to know the k-lines, 
	    # to label them properly and therefore we need to know what lattice we have
	    if self.getkLines:
		if 'lattice' in self.data:
		    kLines, kLinesDict = getkLines(self.workdir, DirectLattice=self.data['lattice'])
		    self.data['kLines'] = kLines
		    self.data['kLinesDict'] = kLinesDict
		else:
		    self.log.warning('\tCould not interpret the kLines info without a given lattice in mind'
                                      '\tMake sure data[''lattice''] is specified before quering the band-structure')
		
            if self.prepareforplot and self.getkLines and 'lattice' in self.data:
                bandsPlt,kLinesPlt = rmEquivkPts(bs.getBands(E0=self.Eref)[0], # note that getBands returns (bands,E0)
                                                kLines, self.data.get('equivkpts',[]))
                self.data['bandsPlt'] = bandsPlt
                self.data['kLinesPlt'] = greekLabels(kLinesPlt)
                
                
    def __call__(self):
        self.query()
