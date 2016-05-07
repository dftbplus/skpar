"""
Routines to handle input files in yaml.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from matplotlib import cm
import numpy as np
import yaml
#import pprint
from collections import OrderedDict
import logging
import sys

def normalise(a):
    """Normalise the given input array.

    Args:
        a (array): input array

    Returns:
        a/norm (array): The norm is the sum of all elements across all dimensions.
    """
    norm = np.sum(a)
    return a/norm

def loadyaml (file, cue):
    """Load yaml file and return the contents of the given cue.

    Crawls through each document in the yaml `file` and looks for a key=`cue`.
    Returns the value corresponding to the `cue`, or exits with error.

    Args:
        file (filename): Input Yaml file
        cue (string): Key to extract from the Yaml file
    
    Returns:
        data (dict): The value of the cue in the yaml document,
            if found; Exits with error if cue not found.
    """

    docs = yaml.load_all(open(file))
    for doc in docs:
        try:  
            data = doc[cue] 
            return data
        except KeyError:
            pass
    return None
    
def remap(dd, mm):
    """Get a subdicitonary of the input data, with translated keys.
    
    Return only a subset of the key-value pairs in `dd`, according 
    to the key entries in the provided map `mm` (list of dicts).
    The returned subdictionary is OrderedDict.

    Args:
        dd (dict): input dictionary
        mm (list of dict): a map serving to translate selected keys
            in `dd` with alternative names. So each item in `mm`
            is a dict((newkey, oldkey)).

    Returns:
        newdict (dict): a sub-set of `dd`, where each original key
            has been replaced with a new key, as per `mm`.
    """
    newdict = []
    for item in mm:
        # item is {newkey: oldkey}
        for k, v in item.items():
            newdict.append((k, dd[v]))
    return OrderedDict(newdict)

    
class RefData (object):
    """Reference Data Object.

    This class encapsulates a group of reference items obtained from
    a data file; It sets up a global weight for the group of data
    items, and sub-weights for the relative importance of each individual
    data item within the group.
    """
    loaders = {"np.loadtxt": np.loadtxt, 
              "yaml": loadyaml}
    def __init__(self, ref, cue, **kwargs):
        """Initialise reference data structure and weights from user input.

        Assumed is that the user input `ref` specifies how to get data
        from files that contain it. By `How` we mean what file, how to
        read it, how to interpret the data, what weights to associate with
        each data item, and what weight of importance to associate with
        the entire group of data items tagged by `cue`.

        The following attributes are available after initialisation:
            * the value of `cue`: (setattr(self, cue, data) is used, where
                `data` is initialised from a file specified in `ref`
            * weight: global weight for the created instance
            * subweights: individual weights of relative importance, for 
                each item in `data`. If `data` is an array, subweights will
                have the same shape. If `data` is a list or OrderedDict, 
                subweights will have the same length.

        NOTABENE: 
            `ref` does not contain the data; it merely hold description of
            how to get it.

        The following content of `ref` is handled within the current method:
            {'file': 'data_file'} mandatory.
            {'loader': 'loader_routine'} optional; default np.loadtxt;
                name of the function to use to read the `data_file`.
                Currently supported are ['np.loadtxt', 'loadyaml'].
            {'loader_args': {dict of keyword args} passed as **kwargs to the
                loader routines. e.g. 'skiprows' or 'unpack' to np.loadtxt.
            {'weight': value} Group weight, meant as a relative importance
                with respect to other `cue`s in `ref`. Default is 1.0.
        
        Args:
            ref (dict): Dictionary with input reference data.
            cue (string): Cue or tag or name of a group of data items to
                be extracted from `ref`.
            kwargs (dict): keyword arguments supplied to the loader of a 
                the actual reference data.

        Returns:
            None
        """
        logger = logging.getLogger('skopt')
        if cue in ref.keys():
            if not ref[cue].get('ignore', False):
                # assuming `ref` is a general dictionary object,
                # we first extract its 'cue' only
                self.ref = ref[cue]
                # how to load the data
                file     = self.ref['file']
                #
                dflt_loader = kwargs.get('dflt_loader', 'np.loadtxt')
                loader      = self.ref.get('loader', dflt_loader)
                #
                dflt_loader_args = kwargs.get('dflt_loader_args', {})
                loader_args      = self.ref.get('loader_args', dflt_loader_args)
                # The major part: the reference data goes under the same cue(name)
                # and we specify default subweights, and a global weight for the cue.
                setattr(self, cue, self.loaders[loader](file, **loader_args))
                setattr(self, 'weight', self.ref.get('weight', 1.0))
                cuedata = getattr(self, cue)
                try:
                    shape = cuedata.shape
                except AttributeError:
                    shape = len(cuedata)
                setattr(self, 'subweights', np.ones(shape))
        else:
            logger.critical("Reference data cue '{}' not found".format(cue))
            sys.exit(2)

class RefYaml (RefData):
    """Reference data initialised from Yaml data files.
    """
    def __init__(self, ref, cue):
        dflts = {'dflt_loader': 'yaml',
                 'dflt_loader_args': {'cue': cue},
                 }
        RefData.__init__(self, ref, cue=cue, **dflts)
        # translate keys() to the convention of SKOPT
        self.map = self.ref.get('map', None)
        if self.map is not None:
            setattr(self, cue, remap(getattr(self, cue), self.map))
        # set subweights if any are explicitly provided
        # we make sure that subweights match the length of self.cue
        # after the remapping, which may have filtered some items
        setattr(self, 'subweights', np.ones(len(getattr(self, cue))))
        try:
            for key, val in self.ref['subweights'].items():
                # note that cuedata is ordered dictionary and 
                # we must ensure correspondence for the subweights
                ix = list(getattr(self, cue).keys()).index(key)
                self.subweights[ix] = val
        except KeyError:
            # no subweights specified
            pass
        self.subweights = normalise(self.subweights)

        
class RefBands (RefData):
    """Reference Band-structure.

    The actual data would typically come from DFT calculations. 
    Assuming N bands and M k-points, the file storing the full BS 
    will have M lines with N or N+1 columns, depending on whether 
    kpoint-index is included or not:

        kpt_index E(band1) E(band2) E(band3) .... E(bandN)

    These would be imported by:

        bands = np.loadtxt("bands_tot.dat", unpack=True)[1:,]

    which will eliminate the band-index, and allow accessing individual 
    bands by, e.g. -- for spin degenerate system:

        topvb = bands[nelectrons-1]
    """
    
    def __init__(self, ref):
        cue = 'bands'
        dflts = {'dflt_loader': 'np.loadtxt',
                 'dflt_loader_args': {'unpack':True},
                 }
        RefData.__init__(self, ref, cue=cue, **dflts)
        if self.ref.get('enumerate', True):
            # if k-points are enumerated in the datafile, then at this
            # stage they would appear as bands[0], so we remove them
            self.bands = np.delete(self.bands, 0, 0)
        # how to interpret the bands:
        #   CB offset to match Band-gap? 
        #   what energy to take for 0?
        #   number of electrons (to destinguish VB from CB in insulators)
        eref            = self.ref.get('reference_energy', 0)
        bandgap         = self.ref.get('bandgap', None)
        self.nelectrons = self.ref.get('nelectrons', 0)
        # shift energy reference if needed
        if eref == 'vbtop':
            assert self.nelectrons > 0
            self.eref = max(self.bands[self.nelectrons-1])
        else:
            self.eref = eref
        self.bands = self.bands - self.eref
        # fix fundamental BG if needed
        if bandgap is not None and self.nelectrons > 0:
            ehomo = max(self.bands[self.nelectrons-1])
            elumo = min(self.bands[self.nelectrons  ])
            deltaEgap = (elumo-ehomo) - bandgap
            self.bands[self.nelectrons: , ] += deltaEgap
        # now deal with the weight, and subweights (per E-k point)
        self.weight = self.ref.get('weight', 1.0)
        # make sure we re-initialise subweights, since bands.shape 
        # may have change after the initialisation in RefData.__init__()
        # due to enumerate=True
        self.subweights = np.ones(self.bands.shape)
        try:
            for item in self.ref['subweights']['eV']:
                emin, emax, w = item[0][0], item[0][1], item[1]
                self.subweights[(emin < self.bands) & (self.bands < emax) & 
                                (self.subweights < w)] = w
        except KeyError:
            pass
        try:
            for item in self.ref['subweights']['nb']:
                # note below we make the specified range INCLUSIVE of both ends!
                ibmin, ibmax, w = item[0][0], item[0][1]+1, item[1]
                mask = np.where(self.subweights[ibmin: ibmax] < w)                 
                self.subweights[ibmin: ibmax][mask] = w
        except KeyError:
            pass
        self.subweights = normalise(self.subweights)
        # visualise
        self.plotfile = self.ref.get('plot', None)
        if self.plotfile is not None:
            plotargs = self.ref.get('plotargs', {})
            self.plot(outfile=self.plotfile, **plotargs)
            
    def plot(self, figsize=(6, 7), outfile=None, Erange=None, krange=None):
        """Visual representation of the bands-structure and sub-weights.
        """
        fig, ax = plt.subplots(figsize=figsize)
        nb, nk = self.bands.shape
        xx = np.arange(nk)
        ax.set_xlabel('$\mathbf{k}$-point')
        ax.set_ylabel('Energy (eV)')
        if Erange is not None:
            ax.set_ylim(Erange)
        if krange is not None:
            ax.set_xlim(krange)
        else:
            ax.set_xlim(np.min(xx), np.max(xx))
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        if len(np.unique(self.subweights))-1 > 0:
            color = cm.jet((self.subweights-np.min(self.subweights))/
                        (np.max(self.subweights)-np.min(self.subweights)))
        else:
            color = ['b']*nb
        for yy, cc in zip(self.bands, color):
            ax.scatter(xx, yy, s=1.5, c=cc, edgecolor='None')
        if self.plotfile is not None:
            fig.savefig(outfile)
        return fig, ax
