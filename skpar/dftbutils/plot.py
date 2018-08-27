import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import logging

module_logger = logging.getLogger(__name__)

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
    # for some reason None goes as a label; better avoid
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
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

def plot_bs(xx, yy, colors=None, linelabels=None, title=None, figsize=(6,7),
        xticklabels=None, yticklabels=None, xlim=None, ylim=None, 
        xlabel=None, ylabel='Energy (eV)', filename=None,
        legendloc=0, **kwargs):
    """Routine for plotting band-structure.

    Accepts one or more sets of k-vector and corresponding bands,
    but the k-vector may be shared too.
    If you supply a set of ticks and labels for specific k-points,
    it will put them on X axis and will extend the xticks over
    all Y as thin lines; see xticklabels below.

    Args:
        xx: 1D array or a list of such; k-points.shape = nk
        yy: 2D array or a list of such; bands.shape = nk, nE
            Notabene: each band is a column in its respective array
                      so that the lowest band is leftmost.
        colors: list of colors, one per 2D array of bands; if None,
                default matplotlib Vega/D3 set of colours is used.
        linelabels: list of strings to label each set of bands in legend
        title: figure title
        figsize: tupple for figure dimensions, in inches; defaults to (6,7)
        xlim, ylim: tupple of limits for X-axis, or Y-axis
        xlabel, ylabel: axes labels
        xticklabels, yticklabels: a list of explicit X- or Y-axis ticks
                and labels, e.g. [('label',x), ...]
        filename (str): filename (incl directory as needed); if present
            the figure is saved to that file.

    Kwargs:
        kticklabels: interpreted as xticklabels
        eticklabels: interpreted as yticklabels
        No other kwargs are interpreted, but no exception is generated
        if supplied.

    Returns:
        fig, ax: matplotlib objects holding the plot
    """
    set_mplrcpar()
    fig, ax = plt.subplots(figsize=figsize)
    # it is likely to get kticklabels instead of xticklabels
    # than it is xticklabels
    if xticklabels is None:
        xticklabels = kwargs.get('kticklabels', None)
    if yticklabels is None:
        yticklabels = kwargs.get('eticklabels', None)
    set_axes(ax, xlabel, ylabel, xticklabels, yticklabels,
                extend_xticks=True)

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
    # yy is either a 2D array or a list of such
    # xs is either a 1D array or a list of such
    # ------------------------------
    if isinstance(xx, list) and type(xx[0]) is np.ndarray:
        assert xx[0].ndim == 1, (xx[0].shape, xx[0].ndim)
        issetx = True
    else:
        assert xx.ndim == 1, (xx.shape, xx.ndim)
        issetx = False
    if isinstance(yy, list) and type(yy[0]) is np.ndarray:
        assert yy[0].ndim == 2, yy[0].shape
        issety = True
    else:
        assert yy.ndim == 2, yy.shape
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
            lines = ax.plot(xval, yval.transpose(), color=cval[i], label=linelabels[i])
            if linelabels[i]:
                legenditems.append(lines[0])
    else:
        assert not issetx
        xval = xx
        yval = yy
        lines = ax.plot(xval, yval.transpose(), color=cval[0], label=linelabels[0])
        if linelabels[0]:
            legenditems.append(lines[0])

    # set limits at the end, to make sure no artist tries to expand
    set_xylimits(ax, xx, yy, xlim, ylim, issetx, issety)

    if title:
        ax.set_title(title, fontsize=16)

    if legenditems:
        ax.legend(legenditems, linelabels, fontsize=14, loc=legendloc)

    if filename:
        fig.savefig(filename)

    return fig, ax

def magic_plot_bs(xval, yval, filename=None, **kwargs):
    """A magic-wrapper around the fundamental back-end plot_bs function.

    The magic is that if yval is a list of [Egap, VBand, CBand,...] the 
    data is modified so that a band-gap, Egap, is open between cband and vband,
    even if they are not properly aligned, e.g. if CB bottom is 0 at the same
    time as VB top is 0. Note that the CB is moved, not the VB.
    NOTABENE: the order must be Egap, VB, CB!

    We do this here, so that we don't burden the PlotTask elsewhere with
    knowledge of what band structure and band-gap is, and keep it
    independent of what it is plotting. However, somewhere, the gap need
    to be opened, if we've specified CB and VB as independent objectives,
    and certainly the band-end plot_bs is not such a place due to its 
    intended generality (of plotting band-structures unrelated to 
    objectives, optimisation etc.).
    
    The magic happens only if yval contains an array shaped (1,), which is 
    taken as a band-gap. If no such array is discovered, no shifts are applied
    to the bands.

    Args:
        filename(str): valid filename to save the plot
        xval(arr): k-points (1D array or a list of values and 1D arrays)
        yval(arr): bands (2D-array or a list values and 2D arrays)

    Kwargs:
        Check plot_bs for details as kwargs are passed directly to it.

    Returns:
        fig, ax: matplotlib figure and axes objects containing the plot
    """
    # assume that yval is either:
    # [Egap, VB, CB], or – if both model and reference present:
    # [Egap(ref), Egap(model), VB(ref), VB(model), CB(ref), CB(model)], or,
    # [Egap(model), VB(model), CB(model), Egap(ref), VB(ref), CB(ref)], or,
    # [Egap(ref), VB(ref), CB(ref), Egap(model), VB(model), CB(model)]
    # So, we must find if and where we have a single value (Egap) and record
    # the corresponding indexes; later remove these entries from the yval
    # array in preparation to calling the general bandstructure plotting
    # functions.
    # Note that we do not know the reference energy value for CB or VB –
    # it may not be 0.
    shift = []  
    xx, yy = [],[]
    for i in range(len(yval)):
        if yval[i].shape == (1,):
            eg    = yval[i][0]
            if yval[i+1].shape == (1,) or yval[i-1].shape == (1,):
                # Eg1, Eg2, VB1, VB2, CB1, CB2
                evtop = np.max(yval[i+2])
                ecbot = np.min(yval[i+4])
                shift.append((i+2, 0))     
                shift.append((i+4, eg - (ecbot - evtop)))
            else:
                # Eg1, VB1, CB1, Eg2, VB2, CB2
                evtop = np.max(yval[i+1])
                ecbot = np.min(yval[i+2])
                shift.append((i+1, 0))     
                shift.append((i+2, eg - (ecbot - evtop)))
    # sort shift according to i above, so that shifted bands match
    # the order unshifted once, to maintain correspondence with 
    # colors and labels!
    shift.sort(key=lambda x: x[0])
    if shift:
        module_logger.debug('Including band-gap in BS plot; shift: {}'.
                format(shift))
        for i, s in shift:
            yy.append(yval[i] + s)
            if len(xval) == len(yval):
                xx.append(xval[i])
            else:
                assert len(xval) == len(shift), len(xval)
                xx = xval
    else:
        xx = xval
        yy = yval
    module_logger.debug('Calling plot_bs with len(xval)={} and len(yval)={}'.
                        format(len(xx), len(xx)))
    # call the back-end bandstructure plotter with the updated yval
    fig, ax = plot_bs(xx, yy, **kwargs)
    # since we have fig and ax, we could use this to add things related
    # to parameter and fitness by means of text or x-axis label, for example,
    # if the values are communicated by the PlotTask caller.
    fig.savefig(filename)
    plt.close('all')
