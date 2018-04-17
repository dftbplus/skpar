import logging
import numpy as np
import itertools
import os.path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from skpar.core.utils import get_ranges, get_logger
from skpar.core.plot import skparplot
from skpar.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skpar.dftbutils.queryDFTB import get_effmasses, get_special_Ek
from skpar.dftbutils.plot import magic_plot_bs

module_logger = get_logger('skpar.tasks')

def get_model_data (workroot, src, dst, data_key, *args, **kwargs):
    """Get data from file and put it in a dictionary under a given key.

    Use numpy.loadtxt to get the data from `src` file and 
    write the data to `dst` dictionary under `data_key`. 

    Applicable kwargs: 

        * loader_args: dictionary of np.loadtxt kwargs

        * process: dictionary of kwargs:
            
            + rm_columns: [ index, index, [ilow, ihigh], otherindex, [otherrange]] 
            + rm_rows   : [ index, index, [ilow, ihigh], otherindex, [otherrange]] 
            + scale : float=1
    """
    assert isinstance(src, str), \
        "src must be a filename string, but is {} instead.".format(type(src))
    assert isinstance(data_key, str), \
        "data_key must be a string naming the data, but is {} instead.".format(type(data_key))

    fname = os.path.normpath(os.path.join(workroot, os.path.expanduser(src)))
    loader_args = {} #{'unpack': False}
    # overwrite defaults and add new loader_args
    loader_args.update(kwargs.get('loader_args', {}))
    # make sure we don't try to unpack a key-value data
    if 'dtype' in loader_args.keys() and\
        'names' in loader_args['dtype']:
            loader_args['unpack'] = False
    # read file
    try:
        array_data = np.loadtxt(fname, **loader_args)
    except ValueError:
        # `fname` was not understood
        module_logger.critical('np.loadtxt cannot understand the contents of {}'.format(fname)+\
                                'with the given loader arguments: {}'.format(**loader_args))
        raise
    except (IOError, FileNotFoundError):
        # `fname` was not understood
        module_logger.critical('Data file {} cannot be found'.format(fname))
        raise
    # do some filtering on columns and/or rows if requested
    # note that file to 2D-array mapping depends on 'unpack' from
    # loader_args, which transposes the loaded array.
    postprocess = kwargs.get('process', {})
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
    dst[data_key] = array_data

gettaskdict = {
        'get_model_data': get_model_data,
        'get_dftbp_data': get_dftbp_data,
        'get_dftbp_bs'  : get_bandstructure,
        'get_dftbp_meff': get_effmasses,
        'get_dftbp_Ek'  : get_special_Ek,
        }

plottaskdict = {
        'plot_objvs': skparplot,
        'plot_bs'   : magic_plot_bs
        }
