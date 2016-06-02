"""
Classes and functions related to parsing the definition of
objectives in the input file, the declaration of objectives and
their evaluation.
"""
import logging
import yaml
from pprint import pprint, pformat
import numpy as np

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
        n = len(data)
        ww = np.ones(n)*dflt
        _keys, _values = data.dtype.names
        for key, val in spec.items():
            # notabene: the encode() makes a 'string' in b'string'
            ww[data[_keys]==key.encode()] = val
        return ww

def parse_weights(spec, refdata=None, n=1, shape=None, i0=0, 
                  ikeys=None, rikeys=None, rfkeys=None):
    """Parse the specification defining weights corresponding some data.

    The data may or may not be specified, depending on the type of
    specification that is provided. Generally, the specification would
    enumerate either explicit indexes in the data, or a range of
    indexes in the data or a range of values in the data, and would
    associate a weight with the given range.
    
    To give freedom of the user (i.e. the caller), the way that ranges
    are specified is enumerated by the caller by optional arguments --
    see `ikeys`, `rikeys` and `rfkeys` below.
    
    Args:
        spec (dict): specification of the subweights, for example::
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
        n (int): length of `refdata` (and corresponding weights)
        shape (tuple): shape of `reference` data, if it is array but not given
        i0 (int): index to be assumed as a reference, i.e. 0, when 
            enumerating indexes explicitly or by a range specifiaction.
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
    if isinstance(spec, list) and len(spec)==n or\
        type(spec).__module__ == np.__name__:
        # Assume spec enumerates weights as a list or array
        return spec
    else:
        # Parse specification to write out the weights
        # initialise default values
        dflt = spec.get('dflt', 0)
        if shape is None:
            if refdata is not None:
                shape = refdata.shape
            else:
                shape = (n,)
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
        return result


class Objective(object):
    """Decouples the declaration of an objective from its evaluation.

    Objectives are declared by human input data that defines:
        * reference data,
        * options for interpretation of the reference data
        * models (names), from which to obtain model data
        * options for interpretation of the model data (mapping to reference)
        * relative weight of the objective, in the context of multi-objective
          optimisation.

    Instances are callable, and return a triplet of model data, reference data,
    and sub-weights of relative importance of the items within each data.
    """
    def __init__(self, models, ref_data, weight=1., 
                 logger=None, **kwargs):
        """Register the objective.
        """
        self.model_names, self.model_weights = get_models(models)
        self.ref_data = ref_data
        self.weight = weight
        self.doc = kwargs.get('doc', "")
        self.model_options = kwargs.get('model_options', None)
        self.ref_options = kwargs.get('ref_options', None)
        self.logger = get_logger(logger)
              
    def get(self):
        """
        Get the corresponding model data, reference data, and sub-weights.
        This method must be overloaded in a child-class in a way that
        yields self.model_data.
        """
        assert hasattr(self, 'model_data'),\
            "Model data is missing in Objective {}.\n".format(self)+\
            "Please, overload its get method to produce self.model_data."
        assert hasattr(self, 'subweights'),\
            "Sub-weights are missing in Objective {}.\n".format(self)+\
            "Please, overload its __init__() method to produce self.subweights."
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
        s.append ("Model options:\n{}".format(pformat(self.model_options)))
        if hasattr(self, 'model_data'):
            s.append ("Model data:\n{}".format(pformat(self.model_data)))
        else:
            s.append ("Model data not available yet")
        s.append ("Reference data:\n{}".format(pformat(self.ref_data)))
        s.append ("Reference options:\n{}".format(pformat(self.model_options)))
        if hasattr(self, 'subweights'):
            s.append ("Sub-weights:\n{}".format(pformat(self.subweights)))
        else:
            s.append ("Sub-weights not available yet")
        s.append ("Weight: {}".format(self.weight))
        return "\n".join(s)


class ObjValues(Objective):
    """
    """
    def __init__(self, models, ref, weight=1., logger=None, **kwargs):
        super().__init__(cls, models, ref, weight, logger, **kwargs)
        self.query = Query(self.model_names, kwargs.get('query', 'Etot'))
        n = len(model_names)
        if n > 1:
            self.subweights = parse_weights(
                self.ref_options.get('subweights', np.ones(n)),
                n=n, ikeys=["indexes",], irkeys=['ranges'])
            assert self.subweights.shape == self.ref_data.shape
        else:
            self.subweight = 1.
        
    def get(self):
        """
        """
        self.model_data = self.query()
        if len(self.model_names)>1:
            assert self.model_data.shape == self.subweights.shape
        return super().get()


class ObjKeysValues(Objective):
    """
    """
    def __init__(self, models, ref, weight=1., logger=None, **kwargs):
        super().__init__(cls, models, ref, weight, logger, **kwargs)
        # parse reference data options
        options = self.ref_options
        # notabene: we use 'ref' here, and will replace self.ref_data
        n = len(ref)
        ww = parse_weights_map(options.get('subweights', np.ones(n)),
                                            data=ref)
        mask = np.where(ww != 0)
        self.keys = [k.decode() for k in self.ref[0][mask]]
        self.ref_data = self.ref_data[1][mask]
        self.subweights = ww[mask]
        self.queries = []
        for key in self.keys:
            self.queries.append(Query(self.model_names, key))
            
    def get(self):
        self.model_data = []
        for query in self.queries:
            self.model_data.append(query())
        super().get()


class ObjWeightedSum(Objective):
    """
    """
    def __init__(self, models, ref, weight=1., logger=None, **kwargs):
        """
        """
        super__().__init__(cls, models, ref, weight, logger, **kwargs)
        assert len(self.model_names) == len(self.model_weights)
        self.query = Query(self.model_names, kwargs.get('query', 'Etot'))
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
    def __init__(self, models, ref, weight=1., logger=None, **kwargs):
        super().__init__(cls, models, ref, weight, logger, **kwargs)
        #
        # Register relevant queries -- here we have more than one.
        self.queries = []
        self.queries.append(Query(self.model_names, 'bands'))
        self.queries.append(Query(self.model_names, 'num_electrons'))
        self.queries.append(Query(self.model_names, 'spin_degeneracy'))
        assert len(model_names) == 1
        assert len(self.ref_data.shape) == 2
        #
        # Parse ref_options 
        options = self.ref_options
        #
        # If k-points are enumerated in the datafile from which
        # band-structure was read, then they would appear as 
        # bands[0], so we remove them
        if options.get('enumerated_kpts', True):
            self.ref_data = np.delete(self.ref_data, 0, 0)
        #
        # Set band-index reference as needed.
        # Reference band-index should be an int -- not 'vbtop' or 'cbbot'!
        self.ref_ib0 = options.get('ref_band', 0)
        #
        # Set reference energy accordingly
        self._ref_e0 = options.get('ref_energy', 0) 
        if self._ref_e0 == 'vbtop':
            assert self.ref_ib0 > 0
            self.ref_e0 = max(self.ref_data[self.ref_ib0])
        else:
            if self._ref_e0 == 'cbbot':
                assert self.ref_ib0 > 0
                self.ref_e0 = min(self.ref_data[self.ref_ib0])
            else:
                self.ref_e0 = self._ref_e0
        self.ref_data = self.ref_data - self.ref_e0
        #
        # Fix fundamental BG if needed
        ref_egap = options.get('set_bandgap', False)
        if ref_egap:
            # NOTABENE: here we **assume** ref_ib0 to be i_HOMO
            assert hasattr(self, ref_ib0 > 0)
            ihomo = self.ref_ib0
            ilumo = self.ihomo + 1
            ehomo = max(self.ref_data[ihomo])
            elumo = min(self.ref_data[ilumo])
            deltaEgap = ref_egap - (elumo-ehomo)
            self.ref_data[ilumo: , ] += deltaEgap
        #
        # Parse subweights for E-k points
        shape = self.ref_data.shape
        self.subweights = parse_weights(
            options.get('subweights', np.ones(*shape)),\
            ref_data=self.ref_data, i0=self.ref_ib0,\
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
            bs_plot(outfile=self.plotfile, **plotargs)
            
    def get():
        """
        """
        bands  = next([q for q in self.queries if q.key == 'bands'])()
        n_elec = next([q for q in self.queries if q.key == 'num_electrons'])()
        g_spin = next([q for q in self.queries if q.key == 'spin_degeneracy'])()
        i_homo = int(n_elec / g_spin) - 1
        i_lumo = i_homo + 1
        if self._ref_e0 == 'vbtop':
            # this entails model data should also be referenced at vbtop
            self.mod_ib0 == i_homo
            self.mod_e0 == max(bands[i_homo])
        else:
            if self._ref_e0 == 'cbbot':
                # this entails model data should also be referenced at cbbot
                self.mod_ib0 == i_lumo
                self.mod_e0 == min(bands[i_lumo])
            else:
                # here we expect explicit numbers
                self.mod_ib0 == self.model_options.get('ref_band', 0)
                self.mod_e0 == self.model_options.get('ref_energy', 0.)
        assert isinstance(self.mod_e0, float)
        assert isinstance(self.mod_ib0, int)
        self.model_data = bands - self.mod_e0
        assert self.model_data == self.ref_data
        super().get()


objectives_mapper = {
        'values': ObjValues,
        'band_gap': ObjValues,
        'energy_volume': ObjValues,
        'weighted_sum': ObjWeightedSum,
        'reaction_energy': ObjWeightedSum,
        'effective_mass': ObjKeysValues,
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

def get_objective_refdata(data):
    """Parse the input data and return a corresponding array.

    Return the data array, subject to all loading and postprocessing
    of a data file or pass `usr_input` directly if it is numpy.array.
    """
    try:
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
        # dict of key-value data -> transform to structured array
        dtype = [('keys','|S15'), ('values','float')]
        return np.array([(key,val) for key,val in data.items()], dtype=dtype)

    except TypeError:
        # value or a list  -> return array
        return np.array(data)

    except IndexError:
        # already an array  -> return return as is
        # unlikely scenario, since yaml cannot encode numpy array
        return data

