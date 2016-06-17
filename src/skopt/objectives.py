"""
Classes and functions related to the:

    * parsing the definition of objectives in the input file,
    * setting the objectives for the optimizer, and,
    * evaluation of objectives.
"""
import numpy as np
import yaml
from pprint import pprint, pformat
from skopt.utils import get_logger

def parse_weights_keyval(spec, data):
    """Parse the weights corresponding to key-value type of data.

    Args:
        spec (dict): Specification of weights, in a key-value fashion.
            It is in the example format::
                { 'dflt': 0., 'key1': w1, 'key3': w3}
            with w1, w3, etc. being float values.
        data (structured numpy array): Data to be weighted.

            Typical way of obtaining `data` in this format is to use::

                loader_args = {'dtype': [('keys', '|S15'), ('values', 'float')]}
                data = numpy.loadtxt(file, **loader_args)

    Returns:
        numpy.array: weights corresponding to each key in `data`, 
            with the same length as `data`.
    TODO:
        Log warning if a key in `spec` (other than 'dflt') is not found
        in `data`.
    """
    if isinstance(spec, list) or type(spec).__module__ == np.__name__:
        # if spec enumerates weights as a list or array, nothing to do
        assert len(spec)==len(data) 
        return spec
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
        return ww

def parse_weights(spec, refdata=None, nn=1, shape=None, i0=0, 
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
            for example::
            spec = """ """
            dflt: 0 # default value of subweights
            indexes: # explicit indexes of 1d-array
                - [0, 1]
                - [4, 4]
                - [2, 1]
            ranges: # ranges in 1d-array
                - [[1,3], 2]
                - [[3,4], 5]
            nb: # ranges of bands (indexes) in bands (refdata)
                - [[-3, 0], 1.0] # all valence bands
                - [[0, 1], 2.0]   # top VB and bottom CB with higher weight
            eV: # ranges of energies (values) in bands (refdata)
                - [[-0.1, 0.], 4.0]
                - [[0.2, 0.5], 6.0]
            Ek: # explicit (band, k-point) pair (indexes) in bands (refdata)
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
            indexes specification, e.g. ['ranges', 'nb']
        rfkeys (list of strings): list of keys to be parsed for range of
            values specification, e.g. ['eV']

    Returns:
        numpy.array: the weight to be associated with each data item.
    """
    if ikeys is None:
        ikeys = []
    if rikeys is None:
        rikeys = []
    if rfkeys is None:
        rfkeys = []
    if isinstance(spec, list) and len(spec)==nn or\
        type(spec).__module__ == np.__name__:
        # Assume spec enumerates weights as a list or array
        return np.asarray(spec)
    else:
        # Parse specification to write out the weights
        # initialise default values
        dflt = spec.get('dflt', 0)
        if shape is None:
            if refdata is not None:
                shape = refdata.shape
            else:
                shape = (nn,)
        assert shape is not None
        ww = np.ones(shape)*dflt
        # parse alterations for explicit data indexes
        for k in ikeys:
            for i,w in spec.get(k, []):
                try:
                    # assume i0 and i are int
                    ww[i0+i] = w
                except TypeError:
                    # if it turns out i is a tuple, then 
                    # apply the shift only to i[0].
                    # this works if we specify E-k point (band, k-point)
                    # but is somewhat restrictive in the more general context
                    j = (i0+i[0], i[1])
                    ww[j] = w
        # parse alterations for integer ranges of indexes
        for k in rikeys:
            for rng, w in spec.get(k, []):
                # treat the spec range as **inclusive**, hence the +1 on ihi.
                ilo, ihi = i0+rng[0], i0+rng[1]+1
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

def plot(data, weights=None, figsize=(6, 7), outfile=None, 
        Erange=None, krange=None):
    """Visual representation of the band-structure and weights.
    """
    fig, ax = plt.subplots(figsize=figsize)
    nb, nk = data.shape
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
    if weights is not None and len(np.unique(weights))-1 > 0:
        color = cm.jet((weights-np.min(weights))/
                    (np.max(weights)-np.min(weights)))
    else:
        color = ['b']*nb
    for yy, cc in zip(data, color):
        ax.scatter(xx, yy, s=1.5, c=cc, edgecolor='None')
    if plotfile is not None:
        fig.savefig(outfile)
    return fig, ax


class Query(object):
    """Decouple the intent of making a query from actually making it.

    The class has a database of models (dict objects, resolved by name).
    The database is built by calculators who fill the dictionaries
    with relevant data, and call Query.add_modeldb('model_name', dict).
    Note that the calculators will continually update their 
    corresponding model data.

    A query is registered upon instance creation, by stating a model_name
    (or a list thereof) and a key to be queried from the corresponding
    dict(s).

    A query is executed by calling the instance, which returns
    the corresponding data.

    Examples::

        >>> db1 = {'a':1, 'b':2}
        >>> db2 = {'a':3, 'b':4, 'c':7}
        >>> Query.add_modeldb('d1', db1)
        >>> Query.add_modeldb('d2', db2)
        >>> q1 = Query('d1', 'a')
        >>> q2 = Query(['d1', 'd2'], 'b')
        >>> pprint (q1())
        >>> pprint (q2())
        1
        [2, 4]

    TODO:
        It is conceivable to benefit from a multi-key query (be it over a
        single or multiple models), but this is still in the future.
    """
    modeldb = None
    
    @classmethod
    def add_modeldb(cls, name, ref):
        if cls.modeldb is None:
            cls.modeldb = {}
        cls.modeldb[name] = ref
        
    def __init__(self, model_names, key):
        self.model_names = model_names
        self.key = key
            
    def __call__(self):
        if isinstance(self.model_names, list):
            result = []
            for m in self.model_names:
                result.append(Query.modeldb[m][self.key])
        else:
            result = Query.modeldb[self.model_names][self.key]
        return np.asarray(result)


class Objective(object):
    """Decouples the declaration of an objective from its evaluation.

    Objectives are declared by human input data that defines:
        * reference data,
        * models - from which to obtain model data, and possibly model weights,
        * query - the way to obaining data
        * model weights - relative contribution factor of each model,
        * options, e.g. to specify sub-weights of individual reference items,
        * relative weight of the objective, in the context of multi-objective
          optimisation.

    Instances are callable, and return a triplet of model data, reference data,
    and sub-weights of relative importance of the items within each data.
    """
    def __init__(self, spec, logger=None, **kwargs):
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
            logger (obj): Python logging.logger

        Returns: None
        """
        # mandatory fields; may be we should check and inform if not present
        m_names, m_weights = get_models(spec['models'])
        self.model_names = m_names
        self.model_weights = m_weights
        self.ref_data = get_refdata(spec['ref'])
        # optional fields
        self.weight = spec.get('weight', 1)
        self.options = spec.get('options', None)
        self.doc = kwargs.get('doc', '')
        self.logger = get_logger(logger)
        # this may be set here or in a child, if more specific
        self.query_key = spec.get('query', '')
        self.query = Query(self.model_names, self.query_key)
        self.subweights = np.asarray(1)
              
    def get(self):
        """
        Return the corresponding model data, reference data, and sub-weights.
        This method must be overloaded in a child-class if a more
        specific way to yield the model data in required.
        """
        if not hasattr(self, 'model_data'):
            self.model_data = self.query()
        #
        assert self.model_data.shape == self.ref_data.shape
        assert self.model_data.shape == self.subweights.shape
        #
        return self.model_data, self.ref_data, self.subweights
        
    def __call__(self):
        """Executes self.get().
        """
        return self.get()
    
    def __repr__(self):
        s = []
        if hasattr(self, 'doc'):
            pprint(self.doc)
        s.append("Model names:\n{}".format(pformat(self.model_names)))
        if hasattr(self, 'model_weights'):
            s.append("Model weights:\n{}".format(pformat(self.model_weights)))
        s.append ("Options:\n{}".format(pformat(self.options)))
        if hasattr(self, 'model_data'):
            s.append ("Model data:\n{}".format(pformat(self.model_data)))
        else:
            s.append ("Model data not available yet")
        s.append ("Reference data:\n{}".format(pformat(self.ref_data)))
        if hasattr(self, 'subweights'):
            s.append ("Sub-weights:\n{}".format(pformat(self.subweights)))
        else:
            s.append ("Sub-weights not available yet")
        s.append ("Weight: {}".format(self.weight))
        return "\n".join(s)


class ObjValues(Objective):
    """
    """
    def __init__(self, spec, logger=None, **kwargs):
        super().__init__(spec, logger, **kwargs)
        self.query = Query(self.model_names, spec.get('query', 'Etot'))
        nn = len(self.model_names)
        if nn > 1 and self.options is not None:
            subw = self.options.get('subweights', np.ones(nn))
            self.subweights = parse_weights(subw, nn=nn, 
                    # these are optional, and generic enough
                    ikeys=["indexes",], rikeys=['ranges'])
            assert self.subweights.shape == self.ref_data.shape
        else:
            self.subweight = 1.
        
    def get(self):
        """
        """
        self.model_data = self.query()
        if len(self.model_names) > 1:
            assert self.model_data.shape == self.subweights.shape
        return super().get()


class ObjKeyValuePairs(Objective):
    """
    """
    def __init__(self, spec, logger=None, **kwargs):
        super().__init__(spec, logger, **kwargs)
        # parse reference data options
        options = spec.get('options', None)
        # NOTABENE: we will replace self.ref_data, trimming the 
        #           items with null weight
        nn = len(self.ref_data)
        ww = parse_weights_keyval(options.get('subweights', np.ones(nn)),
                                            data=self.ref_data)
        mask = np.where(ww != 0)
        self.keys = [k.decode() for k in self.ref_data[0][mask]]
        self.ref_data = self.ref_data[1][mask]
        self.subweights = ww[mask]
        assert self.subweights.shape == self.ref_data.shape
        assert len(self.keys) == len(self.ref_data)
        self.queries = []
        for key in self.keys:
            self.queries.append(Query(self.model_names, key))
            
    def get(self):
        model_data = []
        for query in self.queries:
            model_data.append(query())
        self.model_data = np.array(model_data).reshape(self.ref_data.shape)
        super().get()


class ObjWeightedSum(Objective):
    """
    """
    def __init__(self, spec, logger=None, **kwargs):
        """
        """
        super__().__init__(spec, logger, **kwargs)
        self.query = Query(self.model_names, self.query)
        self.subweights = 1.
        
    def get(self):
        """
        """
        summands = self.query()
        assert len(summands) == len(self.model_weights)
        self.model_data = np.dot(summands, self.model_weights)
        return super().get()


class ObjBands(Objective):
    """
    """
    def __init__(self, spec, logger=None, **kwargs):
        super().__init__(spec, logger, **kwargs)
        #
        # Register relevant queries -- here we have more than one.
        self.queries = []
        self.queries.append(Query(self.model_names, 'bands'))
        self.queries.append(Query(self.model_names, 'num_electrons'))
        self.queries.append(Query(self.model_names, 'spin_degeneracy'))
        assert len(model_names) == 1, "Bands-type objective is limited to one model only"
        assert len(self.ref_data.ndim) == 2
        #
        # Parse ref_options 
        options = spec.get('options', None)
        #
        if 'ref_band' in options and 'ref_energy' in options:
            # Set band-index reference as needed.
            # Reference band-index should be an int or a 2-tuple, not 'vbtop' or 'cbbot'!
            self.ib0 = options.get('ref_band', [1, 1])
            if not isinstance(self.ib0, list):
                self.ib0 = [self.ib0]*2
            # note that user input counts from 1, but in python we do from 0:
            self.ib0[0] -= 1
            self.ib0[1] -= 1
            # Set reference energy accordingly
            _e0 = options.get('ref_energy', 0) 
            self.e0_key = None
            self.e0 = _e0
            if _e0 in ['vbtop', 'homo']:
                assert self.ib0 > 0
                self.e0_key = _ref_e0
                self.e0 = max(self.ref_data[self.ib0])
            if _e0 in ['cbbot', 'lumo']:
                assert self.ib0 > 0
                self.e0_key = _e0
                self.e0 = min(self.ref_data[self.ib0])
            if isinstance(_e0, dict) and 'fermi' in _e0.keys():
                self.e0_key = _e0
                self.e0 = _e0['fermi']
        if 'ref_Ek' in options:
            # assume it is list of two two-tupples, for ref_data and for model
            ib0_r, e0_r = options['ref_Ek'][0]
            ib0_m, e0_m = options['ref_Ek'][1]
            self.ib0   = [ib0_r-1, ib0_m-1]
            self.e0    = [e0_r, e0_mj]

        self.ref_data = self.ref_data - self.e0
        #
        # Fix fundamental BG if needed
        ref_egap = options.get('set_bandgap', False)
        if ref_egap:
            # NOTABENE: here we **assume** ref_ib0 to be i_HOMO
            assert hasattr(self, e0_key) and self.e0_key in ['vbtop' or 'homo']
            ihomo = self.ib0
            ilumo = ihomo + 1
            ehomo = max(self.ref_data[ihomo])
            elumo = min(self.ref_data[ilumo])
            deltaEgap = ref_egap - (elumo-ehomo)
            self.ref_data[ilumo: , ] += deltaEgap
        #
        # Parse subweights for E-k points
        shape = self.ref_data.shape
        self.subweights = parse_weights(
            options.get('subweights', np.ones(*shape)),\
            ref_data=self.ref_data, i0=self.ib0,\
            ikeys=['Ek'], rikeys=['nb'], rfkeys=['eV'])
        assert self.subweights.shape == self.ref_data.shape
        #
        # Hack reference data, reducing its shape by eliminating
        # entries with 0 weights
        mask = np.where(self.subweights != 0)
        self.ref_data == self.ref_data[mask]
        self.subweights == self.subweights[mask]
        #
        # Plot reference data and subweights if requested
        plotfile = options.get('plot', None)
        if plotfile is not None:
            plotargs = options.get('plotargs', {})
            plot(self.ref_data, self.subweights, outfile=plotfile, **plotargs)
            
    def get():
        """
        """
        bands  = next([q for q in self.queries if q.key == 'bands'])()
        n_elec = next([q for q in self.queries if q.key == 'num_electrons'])()
        g_spin = next([q for q in self.queries if q.key == 'spin_degeneracy'])()
        i_homo = int(n_elec / g_spin) - 1
        i_lumo = i_homo + 1
        if self.e0_key in ['vbtop', 'homo']:
            # this entails model data should also be referenced at vbtop
            self.ib0[1] == i_homo
            self.e0[0] == max(bands[i_homo])
        if self.e0_key in ['cbbot', 'lumo']:
            # this entails model data should also be referenced at cbbot
            self.ib0[1] == i_lumo
            self.e0[1] == min(bands[i_lumo])
        if self.e0_key == 'fermi':
            e_fermi = next([q for q in self.queries if q.key == 'fermi_energy'])()
            self.e0[1] == e_fermi
        self.model_data = bands - self.e0[1]
        assert self.model_data == self.ref_data
        super().get()


objectives_mapper = {
        'values': ObjValues,
        'band_gap': ObjValues,
        'energy_volume': ObjValues,
        'weighted_sum': ObjWeightedSum,
        'reaction_energy': ObjWeightedSum,
        'effective_mass': ObjKeyValuePairs,
        'bands': ObjBands,
        }

def f2prange(rng):
    """Convert fortran range definition to a python one.
    
    Args:
        rng (2-sequence): [low, high] index range boundaries, 
            inclusive, counting starts from 1.
            
    Returns:
        2-tuple: (low-1, high)
    """
    lo, hi = rng
    msg = "Invalid range specification {}, {}".format(lo, hi)\
        + "Range should be of two integers, both being >= 1."
    assert lo >= 1 and hi>=lo, msg
    return lo-1, hi

def getranges(data):
    """Return list of tuples ready to use as python ranges.

    Args:
        data (int, list of int, list of lists of int):
            A single index, a list of indexes, or a list of
            2-tuple range of indexes in Fortran convention,
            i.e. from low to high, counting from 1, and inclusive
    
    Return:
        list of lists of 2-tuple ranges, in Python convention -
        from 0, exclusive.
    """
    try:
        rngs = []
        for rng in data:
            try:
                lo, hi = rng
            except TypeError:
                lo, hi = rng, rng
            rngs.append(f2prange((lo, hi)))
        return rngs

    except TypeError:
        # data not iterable -> single index, convert to list of lists
        return [f2prange((data,data))]

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
    try:
        # assume `data` contains an instruction where/how to obtain values
        # ----------------------------------------------------------------------
        # NOTABENE:
        # The line below leads to "DeprecationWarning: using a # non-integer 
        # number instead of an integer will result in an error in the future"
        # if `data` happens to be a numpy array already.
        # Some explicit type-checking may be necessary as a rework, since
        # currently we rely on IndexError exception to catch if `data` is 
        # actually an array, but it is not clear if the same exception will be
        # raised in the future.
        # ----------------------------------------------------------------------
        file = data['file']
        # actual data in file -> load it
        # set default loader_args, assuming 'column'-organised data
        loader_args = {'unpack': True}
        # overwrite defaults and add new loader_args
        loader_args.update(data.get('loader_args', {}))
        # read file
        array_data = np.loadtxt(file, **loader_args)
        # do some filtering on columns and/or rows if requested
        # note that file to 2D-array mapping depends on 'unpack' from
        # loader_args, which transposes the loaded array.
        postprocess = data.get('process', {})
        if postprocess:
            if 'unpack' in loader_args.keys() and loader_args['unpack']:
                key1, key2 = ['rm_columns', 'rm_rows']
            else:
                key1, key2 = ['rm_rows', 'rm_columns']
            for axis, key in enumerate([key1, key2]):
                rm_rngs = postprocess.get(key, [])
                if rm_rngs:
                    indexes=[]
                    # flatten, combine and sort, then delete data axis,
                    for rng in getranges(rm_rngs):
                        indexes.extend(list(range(*rng)))
                    indexes = list(set(indexes))
                    indexes.sort()
                    #print ('indexes {}: {}'.format(key, indexes))
                array_data = np.delete(array_data, obj=indexes, axis=axis)
            scale = postprocess.get('scale', 1)
            array_data = array_data * scale
        return array_data

    except KeyError:
        # `data` is a dict of key-value data -> transform to structured array
        dtype = [('keys','|S15'), ('values','float')]
        return np.array([(key,val) for key,val in data.items()], dtype=dtype)

    except TypeError:
        # `data` is a value or a list  -> return array
        return np.array(data)

    except IndexError:
        # `data` is already an array  -> return as is
        # unlikely scenario, since yaml cannot encode numpy array
        return data

def set_objectives(spec, logger=None):
    """Parse user specification of Objectives, and return a list of Objectives for evaluation.

    Args:
        spec (list): List of dictionaries, each dictionary being a,
            specification of an objective of a recognised type.

    Returns:
        list: a List of instances of the Objective sub-class, each 
            corresponding to a recognised objective type.
    """
    objectives = []
    # the spec list has definitions of different objectives
    for objtv in spec:
        # each item in the list is a dictionary (of one key-value pair)
        for key, val in objtv.items():
            # By default, we also pass key as a query, if query is
            # not explicitly defined
            if 'query' not in val.keys():
                val['query'] = key
            objectives.append(
                # We must select the right handler as per spec type
                objectives_mapper.get(key, ObjValues)(val, logger=logger))
    return objectives


