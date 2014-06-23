import os
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


