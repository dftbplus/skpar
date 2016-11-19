"""
Routines to handle input files in yaml and data files (with array-like floats).
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
import os
import sys
from skopt.utils      import normalise
from skopt.objectives import set_objectives
from skopt.query      import Query
from skopt.tasks      import set_tasks
from skopt import tasks

def get_input_yaml(filename):
    """
    """
    with open(filename, 'r') as fp:
        try:
            spec = yaml.load(fp)
        except yaml.YAMLError as exc:
            # this should go to a logger...?
            print (exc)
    return spec

def parse_input(spec):
    objectives = set_objectives(spec['objectives'])
    tasks      = set_tasks(spec['tasks'])

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

def loadyaml (file, key=None, **kwargs):
    """Load yaml file and return the contents of selected key."""
    doc = yaml.load(open(file))
    if key is not None:
        try: 
            data = doc[key]
            return data
        except KeyError:
            return None
    return doc

def get_file_data(data, file=None, logger=None, **kwargs):
    """Update the input dictionary with items from file.
    
    The input dictionary `data` may or may not contain an item 'file'.
    If it does, or alternatively, if `file` is provided, then 
    the file-data is loaded according to its extension:
        * .yaml and .yml files are read into a dict and the dict
          is then updated with the input dictionary `data`.
        * .dat, .txt, .data files are assumed to be arrays and
          readin via np.loadtxt() and the array is added as a new
          item: data['data'] = np.loadtxt()
          
    The updated `data` dictionary is returned.
    
    Remark:
        Items in `data` overwrite items in from `file` or `data['file']`.
    
    Args:
        data (dict): the input dictionary
        file (str):  filename, alternative for loading additional data
        
    Returns:
        data (dict): extended with entries from files
    """
    if logger is None:
        logger = logging.getLogger('__name__')
    try:
        if 'file' not in data.keys():
            if file is not None:
                data['file'] = file
            else:
                return data
    except AttributeError: # data not a dictionary
        return data
    try:
        _file = data['file']
        # instruction in the 'file' override caller instructions
        _loader_args = kwargs.get('loader_args', {})
        _loader_args.update(data.get('loader_args', {}))
        try:
            # caller gives specific instructions how to load the file
            _loader = kwargs['loader']
        except KeyError:
            # try to guess appropriate loader by extension
            if os.path.splitext(_file)[-1] in ['.yaml', '.yml']:
                _loader = loadyaml
            if os.path.splitext(_file)[-1] in ['.dat', '.txt', '.data']:
                _loader = np.loadtxt
        logger.info('Reading data from {} with {}: {}'.
                    format(_file, _loader, _loader_args))
        file_data = _loader(_file, **_loader_args)
        # Now deal with file data:
        try:
            # Loader delivered a dictionary: update it with entries from data
            # Note: we want the entries in the upper file to override
            # the loaded file, hence we update file_data, not 
            # the other way around
            file_data.update(data)
            data = file_data
        except AttributeError:
            # Loader delivered array (or something else): add a new 'data' entry
            # so that the array can be addressable as a whole
            data['data'] = file_data
    except FileNotFoundError:
        logger.critical('File not found: {}'.format(_file))
        sys.exit(2)
    return data

def get_all_data (data, file=None):
    """
    """
    if isinstance(data, dict):
        data = get_file_data(data, file)
        for key, _data in data.items():
            _data = get_all_data(_data)
    if isinstance(data, list):
        for _data in data:
            _data = get_all_data(_data)
    return data
    

class System (object):
    """
    A system is a named ('name' attribute) abstraction layer of the 
    calculations and analysis that can be performed over a given well
    defined entity, for example an atomic structure.
    Properties are calculated by 'tasks' (a list of functions).
    Tasks are a mixture of auxiliary executable and analyser functions
    (typically user provided functions for post-processing the
    data output from auxiliary executable).
    The sequence of task execution is predefined by the user, and
    the actual execution of the tasks populates the 'calculated' 
    dictionary of the system (could be a nested dictionary).
    A system has by default 'refdata' and 'weights', defining the
    reference data and weights of each reference datum.
    The 'updatesystem' method can optionally be supplied, permitting
    the system's environment to be updated based on some call arguments.
    Note that updatesystem is user provided and can have whatever
    interface, unlike tasks, which would typically not accept 
    arguments supplied at runtime. Default method is skipSystemUpdate (pass).
    Additional attributes can be supplied as keyword arguments.
    """
    def __init__(self, ini_data, logger=None):
        """
        Args:
            ini_data (dict): input data
            logger (logging.logger): logger for message reporting
        Returns:
            system (object): instance of a System, initialised
        """
        self.name       = ini_data['name']
        self.workdir    = ini_data.get('dir', self.name)
        self.weight     = ini_data.get('weight', 1.0)
        self.refdata    = ini_data.get('refdata', None)
        self.refweights = ini_data.get('refweights', None)
        self.tasks      = ini_data.get('tasks', [])
        self.update     = ini_data.get('update', lambda: None)
        self.modeldata  = ini_data.get('modeldata', {})
                            # because different analysers will
                            # put data in unpredictable order
        if logger is None:
            self.logger  = logging.getLogger('__name__')

        # set any optional attributes that don't need a default value
        for key, val in ini_data.items():
            if key not in self.__dict__:
                setattr(self, key, val)
    
    def execute(self):
        """
        TODO: should check task exit status, especially for 
              auxiliary executables!
        """
        for task in self.tasks:
            self.log.debug('{0}.{1}'.format(self.name,task))
            try:
                if task.log is None:
                    task.log is self.log
            except AttributeError:
                pass
            task()
        # should return task exit status or something
        return None
            
    def __call__(self):
        return self.execute()


class RefData (object):
    """Reference Data.
    """
    mandatoryattr = {'ignore': False, 
                     'data': None, 
                     'weight': 1.0,
                     'doc': ''}
    def __init__(self, ini_data, logger=None, **kwargs):
        """Initialise reference data structure from user input"""
        if logger is None:
           logger = logging.getLogger('__name__')
        # if not data but a file is given, load it in          
        data = get_file_data(ini_data, logger=logger, **kwargs)
        # set the mandatory attributes with defaults if necessary 
        # and hook the initialisation data as attribute to be
        # accessible to children
        for key, val in self.mandatoryattr.items():
            setattr(self, key, ini_data.get(key, val))
        if self.data is not None:
            try:
                # if data is array
                shape = self.data.shape
                setattr(self, 'subweights', np.ones(shape))
            except AttributeError:
                # if data is not array, it should be parsed further
                # so subweights will be established later
                pass
        self.ini_data = ini_data


class RefYaml (RefData):
    """Reference data initialised from Yaml data files.
    """
    def __init__(self, ini_data, logger=None, **kwargs):
        if logger is None:
            logger = logging.getLogger('__name__')
        dflts = {'loader': loadyaml,
                 'loader_args': {},
                 }
        # allow kwargs to overwrite dflts
        dflts.update(kwargs)
        kwargs = dflts.update(kwargs)
        # get all key-value pairs of ini_data
        RefData.__init__(self, ini_data, logger=logger, **kwargs)
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
    
    def __init__(self, ini_data, logger=None, **kwargs):
        if logger is None:
            logger = logging.getLogger('__name__')
        dflts = {'loader': np.loadtxt,
                 'loader_args': {'unpack':True},
                 }
        # allow kwargs to overwrite dflts
        logger.debug("RefBands kwargs: {}".format(kwargs))
        # update defaults from input data
        for key in dflts.keys():
            if key in ini_data.keys():
                dflts[key] = ini_data[key]
        # overwrite defaults with caller directives
        dflts.update(kwargs)
        RefData.__init__(self, ini_data, logger=logger, **dflts)
        if self.ini_data.get('enumerate', True):
            # if k-points are enumerated in the datafile, then at this
            # stage they would appear as bands[0], so we remove them
            self.data = np.delete(self.data, 0, 0)
        # how to interpret the bands:
        #   CB offset to match Band-gap? 
        #   what energy to take for 0?
        #   number of electrons (to destinguish VB from CB in insulators)
        eref            = self.ini_data.get('reference_energy', 0)
        bandgap         = self.ini_data.get('band_gap', None)
        self.nelectrons = self.ini_data.get('num_electrons', 0)
        self.g_spin     = self.ini_data.get('spin_degeneracy', 2)
        if self.nelectrons > 0:
            self.nvb = int(self.nelectrons / self.g_spin)
        else:
            # set up a time bomb
            self.nvb = -1
        # shift energy reference if needed
        if eref == 'vbtop':
            assert self.nvb > 0
            self.eref = max(self.data[self.nvb-1])
        else:
            self.eref = eref
        self.data = self.data - self.eref
        # fix fundamental BG if needed
        if bandgap is not None and self.nvb > 0:
            ehomo = max(self.data[self.nvb-1])
            elumo = min(self.data[self.nvb  ])
            deltaEgap = bandgap - (elumo-ehomo)
            logger.debug('Eg {}, Ecb {}, Evb {}, deltaEgap {}'.
                    format(bandgap, elumo, ehomo, deltaEgap))
            self.data[self.nvb: , ] += deltaEgap
        # make sure we re-initialise subweights, since bands.shape 
        # may have change after the initialisation in RefData.__init__()
        # due to enumerate=True
        self.subweights = np.ones(self.data.shape)
        try:
            for item in self.ini_data['subweights']['eV']:
                emin, emax, w = item[0][0], item[0][1], item[1]
                self.subweights[(emin < self.data) & (self.data < emax) & 
                                (self.subweights < w)] = w
        except KeyError:
            pass
        try:
            for item in self.ini_data['subweights']['nb']:
                # note below we make the specified range INCLUSIVE of both ends!
                ibmin, ibmax, w = item[0][0], item[0][1]+1, item[1]
                mask = np.where(self.subweights[ibmin: ibmax] < w)                 
                self.subweights[ibmin: ibmax][mask] = w
        except KeyError:
            pass
        self.subweights = normalise(self.subweights)
        # visualise
        self.plotfile = self.ini_data.get('plot', None)
        if self.plotfile is not None:
            plotargs = self.ini_data.get('plotargs', {})
            self.plot(outfile=self.plotfile, **plotargs)
            
    def plot(self, figsize=(6, 7), outfile=None, Erange=None, krange=None):
        """Visual representation of the band-structure and sub-weights.
        """
        fig, ax = plt.subplots(figsize=figsize)
        nb, nk = self.data.shape
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
        for yy, cc in zip(self.data, color):
            ax.scatter(xx, yy, s=1.5, c=cc, edgecolor='None')
        if self.plotfile is not None:
            fig.savefig(outfile)
        return fig, ax


refdatahandler = {
    'bands': RefBands,
    'ekpts': RefData,
    'meff':  RefData,
    'volume_energy': RefData,
    }

def get_systems(data, logger=None, **kwargs):
    """
    """
    _select = kwargs.get('keys', data.keys())
    if logger is None:
        logger = logging.getLogger('__name__')
    systems = []
    for key, val in data.items():
        if key in _select:
            logger.info('Defining system {}'.format(key))
            # assume default filename for the system.yaml
            _file = 'system_{}.yaml'.format(key)
            # get system.data
            _data = get_file_data(val, _file, logger)
            # create an instance with default attributes
            ss = System(_data, logger)
            # reference data and corresponding weights may need to be 
            # initialised now, if not available in _data
            if ss.refdata is None:
                ss.refdata, ss.refweights = \
                    get_refdata(_data.get('refdata', {}), logger)
    #        # tasks may need to be reinitialised too
    #        ss.tasks = get_tasks(_data.get('tasks', {}), logger)
            systems.append(ss)
    return systems   

def get_refdata(data, logger=None, **kwargs):
    """
    """
    ref_data = []
    ref_weights = []
    for key, val in data.items():
        logger.info ("Parsing reference item {}".format(key))
        kwargs.update({'key': key})
        _ref = refdatahandler.get(key, RefData)(val, logger=logger, **kwargs)
        # Currently the _ref object does not have a .data and .weights
        # fields, but different reference groups, each with a 
        # relative weight and sub-weights for individual reference items
        # within the group. This need to be serialised somehow!
        ref_data.append(_ref.data)
        ref_weights.append(_ref.weights)
    return ref_data, ref_weights

def get_tasks(data, logger=None, **kwargs):
    """
    """
    return None
    
def get_executables(data, logger=None, **kwargs):
    """
    """
    return None

def get_skopt_in(file, logger=None, **kwargs):
    """
    """
    if logger is None:
        logger = logging.getLogger('__name__')
    skopt_in_data = loadyaml(file)
    systems     = get_systems(skopt_in_data['systems'], logger)
#    refdata     = get_refdata(skopt_in_data, logger)
#    tasks       = get_tasks(skopt_in_data, logger)
#    executables = get_executables(skopt_in_data, logger)
