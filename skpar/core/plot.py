import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import itertools
import logging
from skpar.core.utils import get_logger

module_logger = get_logger('skpar.tasks')

def set_mplrcpar(**kwargs):
    """Configure matplotlib rcParams."""
    matplotlib.rcParams.update({'axes.titlesize': kwargs.get('fontsize', 18),\
                                'font.size': kwargs.get('fontsize', 18),\
                                'font.family': kwargs.get('fontfamily', 'sans-serif'),
                                'font.sans-serif': kwargs.get('font', 
                                ['Arial', 'DejaVu Sans', 'Bitstream Vera Sans', 'Lucida Grande', 
                                'Verdana', 'Geneva', 'Lucid', 'Helvetica', 'Avant Garde', 'sans-serif'])})
    plt.rc('lines', linewidth=2)
    plt.rc('savefig', bbox='tight')
    plt.rc('savefig', transparent='True')

def set_axes(ax, xlabel, ylabel, xticklabels=None, yticklabels=None,
            extend_xticks=False, extend_yticks=False):
    """Configure axes -- labels and ticks/ticklabels.
    
    Args:
        ax: matplotlib axis object
        xlabel, ylabel (str): labels for the x and y axis
        xticklabels, yticklabels: list of [(value, 'label'), ] for 
            each explicit position of ticks and their labels
        extend_xticks, extend_yticks (bool): extend_x/yticks entire graph
    """
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if xticklabels:
        xticks, xtlabels  = zip(*xticklabels)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xtlabels)
        if extend_xticks:
            [ax.axvline(t, color='k', lw=0.5) for t in xticks]
    else:
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        xticks = None
        xtlabels = None
    if yticklabels:
        yticks, ytlabels  = zip(*yticklabels)
        ax.set_yticks(yticks)
        ax.set_yticklabels(ytlabels)
        if extend_yticks:
            [ax.axhline(t, color='k', lw=0.5) for t in yticks]
    else:
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        yticks = None
        ytlabels = None
    return 

def set_xylimits(ax, xval, yval, xlim=None, ylim=None, issetx=False, issety=False):
    """Set x and y axis limits to exactly fit the data if not explicit.
    
    ax: matplotlib axis object
    xval, yval: array (could be record array), lists of arrays
    xlim, ylim: tupple of (min,max) - explicit axis limits
    issetx, issety (bool): used if xlim or ylim is None, in which case
        these flags serve to tell us to find min and max of the
        xval and yval even if these are record arrays where broadcasting
        won't work. (e.g. yval is an array of two 1D arrays of different shape)
    """
    if ylim:
        ax.set_ylim(ylim)
    else:
        if issety:
            _ymin = [np.min(y) for y in yval]
            _ymax = [np.max(y) for y in yval]
            ax.set_ylim((np.min(_ymin), np.max(_ymax)))
        else:
            ax.set_ylim((np.min(yval), np.max(yval)))
    if xlim:
        ax.set_xlim(xlim)
    else:
        if issetx:
            _xmin = [np.min(x) for x in xval]
            _xmax = [np.max(x) for x in xval]
            ax.set_xlim(np.min(_xmin), np.max(_xmax))
        else:
            ax.set_xlim((np.min(xval), np.max(xval)))
    
def skparplot(xx, yy, colors=None, linelabels=None, title=None, figsize=(6,7),
        xticklabels=None, yticklabels=None, xlim=None, ylim=None, 
        xlabel=None, ylabel=None, filename=None, legendloc=0, 
        withmarkers=False, markers='osv^p*+', markersize=7, 
        extend_xticks=False, extend_yticks=False, **kwargs):
    """General plotting functions for 1D or 2D arrays or sets of these.
    """
    # ------------------------------
    # Plot appearance
    # ------------------------------
    set_mplrcpar()
    fig, ax = plt.subplots(figsize=figsize)
    set_axes(ax, xlabel, ylabel, xticklabels, yticklabels,
                extend_xticks=extend_xticks, extend_yticks=extend_yticks)

    # Colors for each line
    # this is somewhat primitive approach to choosing colors per set
    # with clear defaults
    # cval = ['k', 'r', 'b', 'g', 'c', 'm', 'y'] # colors in old cycler
    # use Vega & D3 color cycler as default (which is now default in matplotlib)
    # ------------------------------
    cval = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
              '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
              '#bcbd22', '#17becf']
    if colors:
        for i in range(len(np.atleast_1d(colors))):
            cval[i] = np.atleast_1d(colors)[i]

    # ------------------------------
    # Figure out how to handle data and plot it
    # yy is either a 1D or 2D array or a list of such
    # xs is either a 1D array or a list of such
    # ------------------------------
    if isinstance(xx, list) and type(xx[0]) is np.ndarray:
        assert xx[0].ndim == 1, (xx[0].shape, xx[0].ndim)
        issetx = True
    else:
        assert xx.ndim == 1, (xx.shape, xx.ndim)
        issetx = False
    if isinstance(yy, list) and type(yy[0]) is np.ndarray:
        assert yy[0].ndim in (1, 2), yy[0].shape
        issety = True
    else:
        assert yy.ndim in (1, 2), yy.shape
        issety = False

    if linelabels:
        if not isinstance(linelabels, list):
            linelabels = [linelabels,]
        if issety and len(linelabels) < len(yy):
            # we've got sets
            # make sure the list of lables matches the number of sets
            module_logger.warning(
                'Missing line labels: {} needed (one per set) but {} found'.
                    format(len(yy), len(linelabels)))
            linelabels.extend([None]*(len(yy)-len(linelabels)))
    else:
        linelabels = [''] * len(yy)

    def _plot(ax, xval, yval, color, label):
        if yval.ndim == 2:
            _yval = yval.transpose()
        else:
            _yval = yval
        lines = ax.plot(xval, _yval, color=color, label=label)
        return lines

    legenditems = []
    if (issety):
        # iterate within sets
        for i in range(len(yy)):
            yval = yy[i]
            if (issetx):
                assert len(xx) == len(yy), (len(xx), len(yy))
                xval = xx[i]
            else:
                xval = xx
            # make sure number of available x-coordinates correspond to the 
            # number of data y-values in each band (line of data):
            # if we have a set of bands: 
            #   yval.shape = nsets, nE, nk
            #   xval.shape = nsets, nk or xval.shape = nk
            assert xval.shape[-1] == yval.shape[-1], (xval.shape, yval.shape)
            lines = _plot(ax, xval, yval, cval[i], linelabels[i])
            if linelabels[i]:
                legenditems.append(lines[0])
    else:
        assert not issetx
        xval = xx
        yval = yy
        lines = _plot(ax, xval, yval, cval[0], linelabels[0])
        if linelabels[0]:
            legenditems.append(lines[0])

    #
    if withmarkers:
        for ll, mm in zip(ax.lines, itertools.cycle(markers)):
            ll.set_marker(mm)
            ll.set_ms(markersize)
            ll.set_mec('b')
            ll.set_mew(1)

    # set limits at the end, to make sure no artist tries to expand
    set_xylimits(ax, xx, yy, xlim, ylim, issetx, issety)

    if title:
        ax.set_title(title, fontsize=16)

    if legenditems:
        ax.legend(legenditems, linelabels, fontsize=14, loc=legendloc)

    if filename:
        fig.savefig(filename)
        plt.close('all')

    return fig, ax


# this routine was left over in objectives. should not be there
# must be checked if it has any value and modified or discarded
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


