import logging
import numpy as np
import os.path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from skpar.core.utils import get_ranges, get_logger
from skpar.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skpar.dftbutils.queryDFTB import get_effmasses, get_special_Ek
from skpar.dftbutils.plot import plotBS

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

def plot_objvs(plotname, xx, yy, colors=None, markers='', ylabels=None, 
        axeslabels=[None, None], xlim=None, ylim=None, figsize=(6, 7), 
        title=None,
        xticklabels=None, yticklabels=None, withmarkers=False, **kwargs):
    """General plotting functions for 1D or 2D arrays or sets of these.
    """
    # ------------------------------
    # Plot appearance
    # ------------------------------
    matplotlib.rcParams.update({'axes.titlesize': kwargs.get('fontsize', 20),\
                                'font.size': kwargs.get('fontsize', 20),\
                                'font.family': kwargs.get('fontfamily', 'sans-serif'),
                                'font.sans-serif': kwargs.get('font', 
                                ['Arial', 'DejaVu Sans', 'Bitstream Vera Sans', 'Lucida Grande', 
                                'Verdana', 'Geneva', 'Lucid', 'Helvetica', 'Avant Garde', 'sans-serif'])})
    plt.rc('lines', linewidth=2)
    fig, ax = plt.subplots(figsize=figsize)

    # ------------------------------
    # Axes decoration
    # ------------------------------
    if axeslabels[0]:
        ax.set_xlabel(axeslabels[0])
    if axeslabels[1]:
        ax.set_ylabel(axeslabels[1])
    if xticklabels:
        ticks, labels  = zip(*xticklabels)
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
    else:
        ax.xaxis.set_minor_locator(AutoMinorLocator())
    if yticklabels:
        ticks, labels  = zip(*yticklabels)
        ax.set_yticks(ticks)
        ax.set_yticklabels(labels)
    else:
        ax.yaxis.set_minor_locator(AutoMinorLocator())

    # ------------------------------
    # Figure out how to handle data
    # ------------------------------
    isset = True if isinstance(yy, list) else False
    if isset:
        module_logger.debug('Plotting a set of {} items:'.format(len(yy)))
        module_logger.debug(' '.join(['{}'.format(item.shape) for item in yy]))
    else:
        module_logger.debug('Plotting an item of length {}:'.format(len(yy)))
    xval = np.asarray(xx)
    # DO NOT DO THAT (line below): if yy is a list of arrays of different shape, 
    # e.g. (4,80), (4,80), (2,80), (2,80), we get garbage: 
    # yval.shape = (len(yy),), in this case, yval.shape=(4,) 
    # instead of (4,?,80), for obvious reasons -- incompatible dim 1 (4 or 2?)
    # The result seems to be an array holding only references to the original arrays.
    # Note that we can still slice it along axis 0 and get job done, but
    # any reference to its higher dimensions will yield mysterious errors!
    yval = np.asarray(yy)
    # the line below fails in the scenario above, which is common if we
    # combine objectives of different dimensions, e.g. CB and VB with different bands.
    # assert xval.shape[-1] == yval.shape[-1], (xval.shape, yval.shape)
    if isset and xval.shape[0] != yval.shape[0]:
        xval = np.tile(xval, len(yval)).reshape(len(yval), len(xval))

    # ------------------------------
    # Deal with colors, markers and labels
    # ------------------------------
    # Get as many colours as necessary; replace with user explicit preferences; 
    # Potentially repeated colors; think about a cure (check if user color in cval)
    #cmap = plt.get_cmap('Set1')
    #cval = [cmap(j) for j in np.linspace(0, 1, 9)]
    cval = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
    if colors:
        for i in range(len(np.atleast_1d(colors))):
            cval[i] = np.atleast_1d(colors)[i]
    #
    if withmarkers:
        mval = [mmap[i%len(mmap)] for i in range(len(yval))]
        for i in range(len(np.atleast_1d(markers))):
            mval[i] = np.atleast_1d(markers)[i]
    else:
        mval = ['']*len(yval)
    ms = kwargs.get('markersize', 7)
    #
    if ylabels:
        ylab = ylabels
        if not len(ylab) == len(yval):
            module_logger.warning('Missing ylabels: {} needed but {} found'.
                    format(len(yval), len(ylab)))
            ylab.extend(['']*(len(yval)-len(ylab)))
    else:
        ylab = ['']*len(yval)

    # ------------------------------
    # Plot the data
    # ------------------------------
    legenditems = []
    for x, y, c, m, l in zip(xval, yval, cval, mval, ylab):
        if y.ndim == 2:
            lines = ax.plot(x, y.transpose(), color=c, marker=m, label=l, ms=ms)
        else:
            lines = ax.plot(x, y, color=c, marker=m, label=l, ms=ms)
        if l:
            legenditems.append(lines[0])
    # set limits at the end, to make sure no artist tries to expand
    ax.set_ylim(ylim)
    ax.set_xlim(xlim)
    if title:
        ax.set_title(title, fontsize=16)
    if ylabels:
        ax.legend(legenditems, ylab)
    fig.savefig(plotname+'.pdf')
    plt.close('all')


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
