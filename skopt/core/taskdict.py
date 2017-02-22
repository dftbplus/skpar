import numpy as np
from os.path import normpath, expanduser
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from skopt.core.utils import get_ranges
from skopt.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skopt.dftbutils.queryDFTB import get_effmasses, get_special_Ek
from skopt.dftbutils.plot import plotBS

def get_model_data (src, dst, data_key, *args, **kwargs):
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
#    data = np.loadtxt(src, **loader_args)
    file = normpath(expanduser(src))
    loader_args = {} #{'unpack': False}
    # overwrite defaults and add new loader_args
    loader_args.update(kwargs.get('loader_args', {}))
    # make sure we don't try to unpack a key-value data
    if 'dtype' in loader_args.keys() and\
        'names' in loader_args['dtype']:
            loader_args['unpack'] = False
    # read file
    try:
        array_data = np.loadtxt(file, **loader_args)
    except ValueError:
        # `file` was not understood
        print ('np.loadtxt cannot understand the contents of {}'.format(file))
        print ('with the given loader arguments: {}'.format(**loader_args))
        raise
    except (IOError, FileNotFoundError):
        # `file` was not understood
        print ('Data file {} cannot be found'.format(file))
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

def plot_objvs(plotname, xx, yy, colors='darkred', markers=None, 
        xlabel='X', ylabel='Y', yyrange=None, xxrange=None, figsize=(6, 7), 
        col='darkred', markersonly=False, withmarkers=False, labels=None, **kwargs):
    """General plotting functions for 1D or 2D arrays.
    """
    matplotlib.rcParams.update({'font.size': kwargs.get('fontsize', 20),\
                                'font.family': kwargs.get('fontfamily', 'sans')})
    plt.rc('lines', linewidth=2)
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    for x, y, c, m in zip(xx, yy, colors, markers):
        if y.ndim == 2:
            ax.plot(x, y.transpose(), color=c, marker=m, markersize=kwargs.get('markersize', 7))
        else:
            ax.plot(x, y, color=c, marker=m, markersize=kwargs.get('markersize', 7))
    # set limits at the end, to make sure no artist tries to expand
    ax.set_ylim(yyrange)
    ax.set_xlim(xxrange)
    fig.savefig(plotname+'.pdf')


gettaskdict = {
        'get_model_data': get_model_data,
        'get_dftbp_data': get_dftbp_data,
        'get_dftbp_bs'  : get_bandstructure,
        'get_dftbp_meff': get_effmasses,
        'get_dftbp_Ek'  : get_special_Ek,
        }

plottaskdict = {
        'plot_objvs': plot_objvs,
        'plot_bs'   : plotBS
        }
