"""
Classes and functions related to the:

    * parsing the definition of objectives in the input file,
    * setting the objectives for the optimizer, and,
    * evaluation of objectives.
"""
import sys
from os.path import normpath, expanduser
from os.path import join as joinpath
from os.path import split as splitpath
import numpy as np
import logging
import yaml
from pprint import pprint, pformat
from skpar.core.utils import get_logger, normalise, arr2s
from skpar.core.utils import get_ranges, f2prange
from skpar.core.database import Query
from skpar.core.evaluate import COSTF, ERRF

DEFAULT_COST_FUNC = "rms"
DEFAULT_ERROR_FUNC = "abs"

LOGGER = get_logger(__name__)

def parse_weights_keyval(spec, data, normalised=True):
    """Parse the weights corresponding to key-value type of data.

    Args:
        spec (dict): Specification of weights, in a key-value fashion.
            It is in the example format::
                { 'dflt': 0., 'key1': w1, 'key3': w3}
            with w1, w3, etc. being float values.
        data (structured numpy array): Data to be weighted.

            Typical way of obtaining `data` in this format is to use::

                loader_args = {'dtype': [('keys', 'S15'), ('values', 'float')]}
                data = numpy.loadtxt(file, **loader_args)

    Returns:
        numpy.array: weights corresponding to each key in `data`, 
            with the same length as `data`.
    TODO:
        Log warning if a key in `spec` (other than 'dflt') is not found
        in `data`.
    """
    if isinstance(spec, list) or isinstance(spec, np.ndarray):
        # if spec enumerates weights as a list or array, nothing to do
        assert len(spec)==len(data) 
        ww = spec
    else:
        # otherwise parse specification to write out the weights
        # initialise default values
        dflt = spec.get('dflt', 0)
        # Key assumption: data is a structured array, where the keys 
        # are already encoded as b'string', hence the use of .encode() below.
        nn = len(data)
        ww = np.ones(nn)*dflt
        _keys, _values = data.dtype.names
        for key, val in spec.items():
            # notabene: the encode() makes a 'string' in b'string'
            ww[data[_keys]==key.encode()] = val
    # normalisation
    if normalised:
        ww = normalise(ww)
    return ww

def parse_weights(spec, refdata=None, nn=1, shape=None, i0=0, normalised=True, 
                  ikeys=None, rikeys=None, rfkeys=None):
    """Parse the specification defining weights corresponding to some data.

    The data may or may not be specified, depending on the type of
    specification that is provided. Generally, the specification would
    enumerate either explicit indexes in the data, or a range of
    indexes in the data or a range of values in the data, and would
    associate a weight with the given range.
    A list of floats is also accepted, and an array view is returned,
    for cases where weights are explicitly enumerated, but no check for length.
    
    To give freedom of the user (i.e. the caller), the way that ranges
    are specified is enumerated by the caller by optional arguments --
    see `ikeys`, `rikeys` and `rfkeys` below.
    
    Args:
        spec (array-like or dict): values or specification of the subweights, 
            for example:

            spec = """ """
            dflt: 1.0 # default value of subweights
            indexes: # explicit [index, weight] for 1d-array data
                - [0, 1]
                - [4, 4]
                - [2, 1]
            ranges: # ranges for 1d-array
                - [[1,3], 2]
                - [[3,4], 5]
            bands: # ranges of bands (indexes) in bands (refdata)
                - [[-3, 0], 1.0] # all valence bands
                - [[0, 1], 2.0]   # top VB and bottom CB with higher weight
            values: # ranges of energies (values) in bands (refdata)
                - [[-0.1, 0.], 4.0]
                - [[0.2, 0.5], 6.0]
            indexes: # explicit (band, k-point) pair (indexes) for bands (refdata)
                - [[3, 4], 2.5]
                - [[1, 2], 3.5]
            """ """

        refdata (numpy.array): Reference data; mandatory only when range of
            values must be specified
        nn (int): length of `refdata` (and corresponding weights)
        shape (tuple): shape of `reference` data, if it is array but not given
        i0 (int): index to be assumed as a reference, i.e. 0, when 
            enumerating indexes explicitly or by a range specification.
        ikeys (list of strings): list of keys to be parsed for explicit 
            index specification, e.g. ['indexes', 'Ek']
        rikeys (list of strings): list of keys to be parsed for range of
            indexes specification, e.g. ['ranges', 'bands']
        rfkeys (list of strings): list of keys to be parsed for range of
            values specification, e.g. ['values', 'eV']

    Returns:
        numpy.array: the weight to be associated with each data item.
    """
    if ikeys is None:
        ikeys = []
    if rikeys is None:
        rikeys = []
    if rfkeys is None:
        rfkeys = []
    if isinstance(spec, list) or isinstance(spec, np.ndarray):
        # Assume spec enumerates weights as a list or array
        ww = np.atleast_1d(spec)
    else:
        # Parse specification to write out the weights
        # initialise default values
        dflt = spec.get('dflt', 1)
        if shape is None:
            if refdata is not None:
                shape = refdata.shape
            else:
                shape = (nn,)
        assert shape is not None
        ww = np.ones(shape)*dflt
        # parse alterations for explicit data indexes
        # convert from FORTRAN to PYTHON, hence the -1 below
        for k in ikeys:
            for i, w in spec.get(k, []):
                try:
                    # assume i0 and i are int
                    ww[i0+i-1] = w
                except TypeError:
                    # if it turns out i is a tuple (i.e. an E-k point), 
                    # then apply the shift only to i[0].
                    # this works if we specify E-k point (band, k-point)
                    # but is somewhat restrictive in the more general context
                    j = (i0+i[0]-1, i[1]-1)
                    ww[j] = w
        # parse alterations for integer ranges of indexes
        for k in rikeys:
            for rngs, w in spec.get(k, []):
                rngs = get_ranges([rngs,])
                for ilo, ihi in rngs:
                    # permit overlapping ranges, larger weight overrides:
                    ww[ilo:ihi][ww[ilo:ihi] < w] = w
        # parse alterations for ranges in the reference data itself
        for k in rfkeys:
            assert refdata.shape == ww.shape
            for rng, w in spec.get(k, []):
                ww[(rng[0] <= refdata) & 
                   (refdata <= rng[1]) &
                   # permit overlapping weights, larger value overrides:
                   (ww < w)] = w
    # normalisation
    if normalised:
        ww = normalise(ww)
    return ww

def get_models(models):
    """Return the models (names) and corresponding weights if any.

    Args:
        models (str, list of str, list of [str: float] items): The 
            string is always a model name. If [str: float] items
            are given, the float has the meaning of weight, associated
            with the model.
    Returns:
        tuple: (model_names, model_weights). Weights
            are set to 1.0 if not found in `models`. Elements of
            the tuple are lists if `models` is a list.
    """
    m_names = []
    m_weights = []
    if isinstance(models, list):
        for mm in models:
            if isinstance(mm, list):
                m_names.append(mm[0])
                m_weights.append(mm[1])
            else:
                m_names.append(mm)
                m_weights.append(1.)
    else:
        m_names = models
        m_weights = 1.
    return m_names, m_weights

def get_type(n_models, ref, dflt_type='values'):
    """Establish the type of objective from attributes of reference and models.
    """
    obj_type = dflt_type
    # If we have more than one model but just one scalar as reference
    # obviously we need scalarization (reduction) routine. We assume
    # the simplest -- weighted sum type; other types must be explicitly 
    # stated
    if n_models > 1 and ref.shape == (1,):
        obj_type = 'weighted_sum' # other types of scalarization must be explicit
    # if we have key-value pairs, then we have key-value type
    if n_models == 1 and ref.ndim == 1 and \
        ref.dtype == [('keys','S15'), ('values','float')]:
        obj_type = 'keyval_pairs'
    # if we have 2D-array ref-data, then we have Bands type
    if n_models == 1 and ref.ndim == 2 and ref.dtype == 'float':
        obj_type = 'bands'
    return obj_type

class Objective(object):
    """Decouples the declaration of an objective from its evaluation.

    Objectives are declared by human input data that defines:
        * reference data,
        * models - from which to obtain model data, and possibly model weights,
        * query - the way to obtaining data
        * model weights - relative contribution factor of each model,
        * options, e.g. to specify sub-weights of individual reference items,
        * relative weight of the objective, in the context of multi-objective
          optimisation.

    Instances are callable, and return a triplet of model data, reference data,
    and sub-weights of relative importance of the items within each data.
    """
    def __init__(self, spec, **kwargs):
        """Instantiate the objective and set non-specific attributes.

        Must be extended to declare a Query and possibly -- CostFunction.
        By 'extend', we mean super().__init__() is called within the 
        child's own __init__().
        That however should be done in a way that is specific to the
        type of objective.

        Args:
            spec (dict): Specification of the objective. Mandatory fields
                are [models, ref], optional keys are [weight, doc,
                options, model_options]

        Returns: None
        """
        self.logger = LOGGER
        self.verbose = kwargs.get('verbose', False)
        if self.verbose:
            self.msg = self.logger.info
        else:
            self.msg = self.logger.debug
        # mandatory fields
        self.objtype = spec['type']
        self.query_key = spec['query']
        self.model_names = spec['model_names']
        self.model_weights = spec['model_weights']
        self.ref_data = spec['ref_data']
        _costf, _errf = spec.get('eval', [DEFAULT_COST_FUNC, DEFAULT_ERROR_FUNC])
        self.costf = COSTF[_costf.lower()]
        self.errf  = ERRF[_errf.lower()]
        # optional fields
        self.weight = spec.get('weight', 1)
        self.options = spec.get('options', None)
        dfltdoc = "{}: {}".format(self.query_key, pformat(self.model_names))
        self.doc = spec.get('doc', dfltdoc)
        # further definitions of set/get depend on type of objective
        # this may be set here or in a child, if more specific
        self.query = Query(self.model_names, self.query_key)
        self.subweights = np.ones(self.ref_data.shape)

    def get(self):
        """
        Return the corresponding model data, reference data, and sub-weights.
        This method must be overloaded in a child-class if a more
        specific way to yield the model data in required.
        """
        #
        assert self.model_data.shape == self.ref_data.shape,\
                    "{} {}".format(self.model_data.shape, self.ref_data.shape)
        assert self.model_data.shape == self.subweights.shape,\
                    "{} {}".format(self.model_data.shape, self.subweights.shape)
        #
        return self.model_data, self.ref_data, self.subweights

    def evaluate(self, database=None):
        """Evaluate objective, i.e. fitness of the current model against the reference."""
        model, ref, weights = self.get(database)
        self.fitness = self.costf(ref, model, weights, self.errf)
        self.summarise()
        return self.fitness

    def summarise(self):
        s = []
        s.append("{:<15s}: {}".format("Objective:", pformat(self.doc)))
        s.append("{:9s}{:<15s}: {}".format("", "Reference data",
                 np.array2string(self.ref_data, precision=3,
                                 suppress_small=True, max_line_width=100)))
        s.append('{:9s}{:<15s}: {}'.format("", "Model data",
                                           np.array2string(self.model_data,
                                                           precision=3,
                                                           suppress_small=True,
                                                           max_line_width=100)))
        s.append('{:9s}{:<15s}: {}'.format("", "Cost", self.fitness))
        self.msg("\n".join(s))

    def __call__(self, database=None):
        """Executes self.evaluate().
        """
        return self.evaluate(database)

    def __repr__(self):
        """Yield a summary of the objective.
        """
        s = []
        s.append("{:9s}{:<15s}: {}".format("", "Objective:", pformat(self.doc)))
        s.append("{:9s}{:<15s}: {}".format("", "Query", self.query_key))
        s.append("{:9s}{:<15s}: {}".format("", "Models", pformat(self.model_names)))
        if hasattr(self, 'model_weights'):
            s.append("{:9s}{:<15s}: {}".format("", "Model weights", 
                    arr2s(self.model_weights)))
        s.append ("{:9s}{:<15s}: {}".format("", "Reference data", 
                arr2s(self.ref_data)))
        if hasattr(self, 'subweights'):
            s.append("{:9s}{:<15s}: {}".format("", "Sub-weights", 
                    arr2s(self.subweights)))
        #s.append ("Options:\n{}".format(pformat(self.options)))
        if hasattr(self, 'Model_data'):
            s.append ('{:9s}{:<15s}: {}'.format("", "Model data",
                    arr2s(self.model_data)))
        s.append("{:9s}{:<15s}: {:s} / {:s}".
            format("", "Cost/Err. func.", self.costf.__name__, self.errf.__name__))
        s.append("{:9s}{:<15s}: {}".format("", "Weight", pformat(self.weight)))
        return "\n"+"\n".join(s)


class ObjValues(Objective):
    """
    """
    def __init__(self, spec, **kwargs):
        super().__init__(spec, **kwargs)
        # if we check len(self.model_names), it returns the string length
        # in the case of single string
        nmod = len(self.model_weights)
        self.nmod = nmod
        # coerce ref-data to 1D array if it is extracted from a 2D array
        if self.ref_data.ndim == 2 and self.ref_data.shape == (1,nmod):
            self.ref_data = self.ref_data.reshape((nmod,))
        self.ref_data.flags.writeable = False
        shape = self.ref_data.shape

        # Process .options and set defaults, in case options is None, or key not present
        if self.options is not None:
            subweights = self.options.get('subweights', None)
            self.normalised = self.options.get('normalise', True)
            align_ref     = self.options.get('align_ref', None)
            align_model   = self.options.get('align_model', None)
        else:
            subweights = None
            self.normalised = True
            align_ref     = None
            align_model   = None

        # Once the ref_data is trimmed, its reference value may be changed
        # so try to parse 'align_ref' option.
        if align_ref is not None:
            shift = get_refval_1d(self.ref_data, align_ref)
            self.ref_data.flags.writeable = True
            self.ref_data -= shift
            self.ref_data.flags.writeable = False


        if subweights is not None:
            self.subweights = parse_weights(subweights,
                    refdata=self.ref_data, nn=nmod,
                    normalised=self.normalised,
                    # these are optional, and generic enough
                    ikeys=["indexes",], rikeys=['ranges'], rfkeys=['values'])
            assert self.subweights.shape == shape, (self.subweights.shape, shape)
        else:
            self.subweights = np.ones(shape)

        # Prepare to shift the model_data values if required
        # The actual shift is applied in the self.get() method
        # since the data is not known at until objective query is
        # executed to get the values of the model data
        self.align_model = align_model

    def get(self, database):
        """Get the model data, align/mask it etc, and return calculated cost.
        """
        # query data base
        self.model_data = np.atleast_1d(self.query(database))
        # apply shift: since model_data is not known in advance
        #              the shift cannot be precomputed; we do it on the fly.
        if self.align_model is not None:
            shift = get_refval_1d(self.model_data, self.align_model)
            self.model_data -= shift
        assert self.model_data.shape == self.subweights.shape,\
                "{} {}".format(self.model_data.shape, self.subweights.shape)
        return super().get()


class ObjKeyValuePairs(Objective):
    """
    """
    def __init__(self, spec, **kwargs):
        super().__init__(spec, **kwargs)
        # parse reference data options
        self.options = spec.get('options', None)
        # NOTABENE: we will replace self.ref_data, trimming the 
        #           items with null weight
        nn = len(self.ref_data)
        # default options
        subweights = None
        normalised = True
        if self.options is not None:
            subweights = self.options.get('subweights', np.ones(self.ref_data.shape))
            normalised = self.options.get('normalise', True)

        # we call parse_weights even with default subweights, which effectively
        # normalises according to 'nomalised'
        ww = parse_weights_keyval(subweights, data=self.ref_data, normalised=normalised)
        # eliminate ref_data items with zero subweights
        mask = np.where(np.invert(np.isclose(ww, np.zeros(ww.shape))))
        self.query_key = [k.decode() for k in self.ref_data['keys'][mask]]
        self.ref_data = self.ref_data['values'][mask]
        self.ref_data.flags.writeable = False
        self.subweights = ww[mask]
        assert self.subweights.shape == self.ref_data.shape
        assert len(self.query_key) == len(self.ref_data)
        self.queries = []
        for key in self.query_key:
            self.queries.append(Query(self.model_names, key))

    def get(self, database):
        self.model_data = np.empty(self.ref_data.shape)
        for ix, query in enumerate(self.queries):
            self.model_data[ix] = (query(database))
        return super().get()


class ObjWeightedSum(Objective):
    """
    """
    def get(self, database):
        """
        """
        summands = self.query(database)
        assert len(summands) == len(self.model_weights)
        self.model_data = np.atleast_1d(np.dot(summands, self.model_weights))
        return super().get()


def get_subset_ind(rangespec):
    """Return an index array based on a spec -- a list of ranges.
    """
    pyrangespec = get_ranges(rangespec)
    subset = []
    for rr in pyrangespec:
        subset.extend(range(*rr))
    return np.array(subset)

def get_refval_1d(array, align, ff={'min': np.min, 'max': np.max}):
    """Return a reference (alignment) value selected from an array.
    
    Args:
        array (1D numpy array): data from which to obtain a reference value.
        align: specifier that could be and index, e.g. 3, or 'min', 'max' 
        ff (dict): Dictionary mapping string names to functions that can
                operate on an 1D array.

    Returns:
        value (float): the selected value
    """
    assert isinstance(align, int) or align in ['min', 'max'],\
            '"align" must be int or "min" or "max".'
    # Transform indexing to python-style, counting from 0, assuming 
    # 'align' came from user specification, fortran-compatible, counting from 1
    ik = align - 1  
    try:
        value = array[ik]
    except TypeError:
        value = ff[align](array)
    return value

def get_refval(bands, align, ff={'min': np.min, 'max': np.max}):
    """Return a reference (alignment) value selected from a 2D array.
    
    Args:
        bands (2D numpy array): data from which to obtain a reference value.
        align: specifier that could be (band-index, k-point), or
                (band-index, function), e.g. (3, 'min'), or ('7, 'max')
        ff (dict): Dictionary mapping strings names to functions that can
                operate on an 1D array.

    Returns:
        value (float): the selected value
    """
    assert isinstance(align[0], int), '"align" must be (int,int) or (int, "min" or "max").'
    # Transform indexing to python-style, counting from 0, assuming 
    # 'align' came from user specification, fortran-compatible, counting from 1
    iband = align[0] - 1  
    try:
        ik = align[1] - 1
        value = bands[iband,ik]
    except TypeError:
        value = ff[align[1]](bands[iband])
    return value


class ObjBands(Objective):
    """
    """
    def __init__(self, spec, **kwargs):
        super().__init__(spec, **kwargs)
        assert isinstance(self.model_names, str),\
            'ObjBands accepts only one model => model_names must be a string, but it is not.'

        # Process .options and set defaults, in case options is None, or key not present
        if self.options is not None:
            rangespec_ref = self.options.get('use_ref', None)
            rangespec_mod = self.options.get('use_model', None)
            align_ref     = self.options.get('align_ref', None)
            align_model   = self.options.get('align_model', None)
            subwspec      = self.options.get('subweights', None)
            self.normalised = self.options.get('normalised', True)
        else:
            rangespec_ref = None
            rangespec_mod = None
            align_ref     = None
            align_model   = None
            subwspec      = None
            self.normalised = True

        # Handle 'use_*' option first, because it leads to exclusion of data
        # NOTABENE: both use_ref and use_model assume that a band-index
        #           corresponds to a row-index in the corresponding array
        if rangespec_ref is not None:
            # Parse the subset index definition
            subset_ind = get_subset_ind(rangespec_ref)
            # Extract only the ref_data corresponding to the subset index
            # This returns a new array; the old ref_data is lost from here on. Do we care?
            self.ref_data = self.ref_data[subset_ind]
            # Since we re-shape self.ref_data, we must reshape 
            # the corresponding subweights too.
            # Note that user spec of subweigths is not parsed yet!
            self.subweights = np.ones(self.ref_data.shape)

        # Once the ref_data is trimmed, its reference value may be changed
        # so try to parse 'align_ref' option.
        if align_ref is not None:
            shift = get_refval(self.ref_data, align_ref)
            self.ref_data -= shift
        self.ref_data.flags.writeable = False

        # Make up a mask to trim model_data if there is use_model
        # Note that the mask is only for dim_0, i.e. to
        # be applied on the bands, over all k-pts, so it
        # is only one one-dimensional array.
        if rangespec_mod is not None:
            # Parse the subset index and record it.
            # Remember that we must apply it at run time after model data acquisition
            self.subset_ind = get_subset_ind(rangespec_mod)
        else:
            self.subset_ind = None

        # Prepare to shift the model_data values if required
        # The actual shift is applied in the self.get() method
        self.align_model = align_model

        shape = self.ref_data.shape
        if subwspec is not None:
            self.subweights = parse_weights(subwspec, refdata=self.ref_data, 
                    normalised=self.normalised, 
                    # the following are optional, and generic enough
                    # "indexes" is for a point in a 2D array
                    # "bands" is for range of bands (rows), etc.
                    # "values" is for a range of values
                    # "krange" may be provided in the future (for column selection),
                    # but is not supported yet
                    ikeys=['indexes','Ekpts'], rikeys=['bands', 'iband'], rfkeys=['values'])
            assert self.subweights.shape == shape
        else:
            if self.normalised:
                self.subweights = np.ones(shape)/self.ref_data.size
            else:
                self.subweights = np.ones(shape)
        
    def get(self, database):
        """Return the value of the objective function.
        """
        # query data base
        self.model_data = self.query(database)
        # apply mask
        # NOTABENE: assumed is that model data is an array in which
        #           a band corresponds to a row
        if self.subset_ind is not None:
            self.model_data = self.model_data[self.subset_ind]
        # apply shift: since model_data is not known in advance
        #              the shift cannot be precomputed; we do it on the fly.
        if self.align_model is not None:
            shift = get_refval(self.model_data, self.align_model)
            self.model_data -= shift
        return super().get()


objectives_mapper = {
        'value'       : ObjValues,
        'values'      : ObjValues,
        'weighted_sum': ObjWeightedSum,
        'keyval_pairs': ObjKeyValuePairs,
        'bands'       : ObjBands,
        }

def get_refdata(data):
    """Parse the input data and return a corresponding array.

    Args:
        data (array or array-like, or a dict): Data, being the 
            reference data itself, or a specification of how to get
            the reference data. If dictionary, it should either
            contain key-value pairs of reference items, or contain
            a 'file' key, storing the reference data.

    Returns:
        array: an array of reference data array, subject to all loading 
            and post-processing of a data file, or pass `data` itself,
            transforming it to an array as necessary.
    """
    if isinstance(data, dict):
        if 'file' in data.keys():
            # `data` contains an instruction where/how to obtain values
            file = normpath(expanduser(data['file']))
            # actual data in file -> load it
            # set default loader_args, assuming 'column'-organised data
            loader_args = {} #{'unpack': False}
            # overwrite defaults and add new loader_args
            loader_args.update(data.get('loader_args', {}))
            # make sure we don't try to unpack a key-value data
            if 'dtype' in loader_args.keys() and\
                'names' in loader_args['dtype']:
                    loader_args['unpack'] = False
            # read file
            try:
                array_data = np.loadtxt(file, **loader_args)
            except ValueError:
                # `file` was not understood
                print ('np.loadtxt cannot understand the contents of {}'\
                        .format(file))
                print ('with the given loader arguments: {}'\
                        .format(**loader_args))
                raise
            except (IOError, FileNotFoundError):
                # `file` was not understood
                print ('Reference data file {} cannot be found'\
                        .format(file))
                raise
            # do some filtering on columns and/or rows if requested
            # note that file to 2D-array mapping depends on 'unpack' from
            # loader_args, which transposes the loaded array.
            postprocess = data.get('process', {})
            if postprocess:
                if 'unpack' in loader_args.keys() and loader_args['unpack']:
                    # since 'unpack' transposes the array, now row index
                    # in the original file is along axis 1, while column index
                    # in the original file is along axis 0.
                    key1, key2 = ['rm_columns', 'rm_rows']
                else:
                    key1, key2 = ['rm_rows', 'rm_columns']
                for axis, key in enumerate([key1, key2]):
                    rm_rngs = postprocess.get(key, [])
                    if rm_rngs:
                        indexes=[]
                        # flatten, combine and sort, then delete corresp. object
                        for rng in get_ranges(rm_rngs):
                            indexes.extend(list(range(*rng)))
                        indexes = list(set(indexes))
                        indexes.sort()
                        array_data = np.delete(array_data, obj=indexes, axis=axis)
                scale = postprocess.get('scale', 1)
                array_data = array_data * scale
            
            return_data = array_data
        else:
            try:
                # `data` is a dict of key-value data -> transform to structured array
                dtype = [('keys','S15'), ('values','float')]
                return_data = np.array([(key,val) for key,val in data.items()], dtype=dtype)
            except TypeError:
                print ('get_refdata cannot understand the contents of data dictionary')
                print ("`data` should contain [string_key: float_value, ] pairs,")
                print ("or has a 'file' key, pointing to a file with data'.")
                print ("Instead get_refdata got", data)
                raise
    else:
        if isinstance(data, np.ndarray):
            # `data` is already an array  -> return as is
            # unlikely scenario, since yaml cannot encode numpy array
            return_data = data
        else:
            # suppose `data` is a value or a list  -> return array
            try:
                return_data = np.atleast_1d(data)
            except TypeError:
                print ('get_refdata cannot understand the contents of data')
                print ('`data` should be np.array, list, value, or dict, but it is not.')
                raise
    return_data.flags.writeable = False
    return return_data

def get_objective(spec, **kwargs):
    """Return an instance of an objective, as defined in the input spec.

    Args:
        spec (dict): a dictionary with a single entry, being
            query: {dict with the spec of the objective}

    Returns:
        list: an instance of the Objective sub-class, corresponding
            an appropriate objective type.
    """
    (key, spec), = spec.items()
    # mandatory fields
    spec['query'] = spec.get('query', key)
    m_names, m_weights = get_models(spec['models'])
    spec['model_names'] = m_names
    spec['model_weights'] = np.atleast_1d(m_weights)
    spec['ref_data'] = get_refdata(spec['ref'])
    if isinstance(m_names, str):
        nmod = 1
    else:
        nmod = len(m_names)
    spec['type'] = spec.get('type', get_type(nmod, spec['ref_data']))
    #   print (spec['type'], spec['query'])
    objv = objectives_mapper.get(spec['type'], ObjValues)(spec, **kwargs)
    #print (objv)
    return objv

def set_objectives(spec, verbose=True, **kwargs):
    """Parse user specification of Objectives, and return a list of Objectives for evaluation.

    Args:
        spec (list): List of dictionaries, each dictionary being a,
            specification of an objective of a recognised type.

    Returns:
        list: a List of instances of the Objective sub-class, each 
            corresponding to a recognised objective type.
    """
    if spec is None:
        LOGGER.error('Missing "objectives:" in user input: nothing to do. Bye!')
        sys.exit(1)
    objectives = []
    # the spec list has definitions of different objectives
    for item in spec:
        objv = get_objective(item, **kwargs)
        objectives.append(objv)
    if verbose:
        LOGGER.info('The following objectives are defined:')
        for objv in objectives:
            LOGGER.info(objv.__repr__())
    return objectives

