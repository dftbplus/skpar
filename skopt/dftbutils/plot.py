import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import logging

module_logger = logging.getLogger(__name__)

def plotBS(plotname, xx, yy, colors=None, markers='', ylabels=None, 
        xlim=None, ylim=[-13, 13], figsize=(6, 7), title=None,
        withmarkers=False, **kwargs):

    """Specialised magic routine for plotting band-structure.
    """
    # ------------------------------
    # Extra data may contain necessary info, if not supplied by primary args
    # ------------------------------
    extra_data = kwargs.get('extra_data', {})

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
    plt.rc('savefig', bbox='tight')
    plt.rc('savefig', transparent='True')
    fig, ax = plt.subplots(figsize=figsize)

    # ------------------------------
    # Axes decoration
    # ------------------------------
    ax.set_xlabel('Wave-vector')
    ax.set_ylabel('Energy, eV')
    # check either kwargs or extra_data for ticks/ticklabels
    xticklabels = kwargs.get('xticklabels', None)
    yticklabels = kwargs.get('yticklabels', None)
    if xticklabels is None:
        # try to get it from extra_data
        try:
            xticklabels = extra_data.get('kticklabels', None)
            # note that items in extra_data may be lists (e.g. item per bands set)
            # but not necessarily, so try to figure that out.
            try:
                # split first label and tick, assuming xticklabels is in a list
                l, t = xticklabels[0][0]
                # obviously we can use only one set of labels and ticks
                xticklabels = xticklabels[0]
            except (ValueError, TypeError) as e:
                # Need more than one value to unpack if xticklabels not in a list.
                # Use directly in such case
                # TypeError if xticklabels is None -- still pass
                pass
        except (KeyError, IndexError) as e:
            pass
    if xticklabels:
        xticks, xtlabels  = zip(*xticklabels)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xtlabels)
    else:
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        xticks = None
        xtlabels = None
    if yticklabels:
        yticks, ytlabels  = zip(*yticklabels)
        ax.set_yticks(yticks)
        ax.set_yticklabels(ytlabels)
    else:
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        yticks = None
        ytlabels = None

    # ------------------------------
    # Figure out how to handle data
    # ------------------------------
    isset = True if isinstance(yy, list) else False
    if isset:
        module_logger.debug('Plotting a set of {} items:'.format(len(yy)))
        module_logger.debug(' '.join(['{}'.format(item.shape) for item in yy]))
    else:
        module_logger.debug('Plotting an item of length {}:'.format(len(yy)))
    xval = np.asarray(xx).copy()
    # DO NOT DO THAT (line below): if yy is a list of arrays of different shape, 
    # e.g. (4,80), (4,80), (2,80), (2,80), we get garbage: 
    # yval.shape = (len(yy),), in this case, yval.shape=(4,) 
    # instead of (4,?,80), for obvious reasons -- incompatible dim 1 (4 or 2?)
    # The result seems to be an array holding only references to the original arrays.
    # Note that we can still slice it along axis 0 and get job done, but
    # any reference to its higher dimensions will yield mysterious errors!
    #yval = np.asarray(yy).copy()
    if isset:
        yval = []
        for aa in yy:
            yval.append(aa.copy())
            yval[-1].flags.writeable = True
        yval = np.asarray(yval)
    else:
        # assume it is a single array or a list of floats
        yval = np.asarray(yy).copy()
    # the line below fails in the scenario above, which is common if we
    # combine objectives of different dimensions, e.g. CB and VB with different bands.
    # assert xval.shape[-1] == yval.shape[-1], (xval.shape, yval.shape)
    if isset and xval.shape[0] != yval.shape[0]:
        xval = np.tile(xval, len(yval)).reshape(len(yval), len(xval))
    
    # ------------------------------
    # Dirty hack to open a band-gap
    # ------------------------------
    # assume that yval is:
    # Egap, VB, CB or
    # Egap(ref), Egap(model), VB(ref), VB(model), CB(ref), CB(model)
    rmix = []
    for i in range(len(yval)):
        if yval[i].shape == (1,):
            if yval[i-1].shape == (1,) or yval[i+1].shape == (1,):
                module_logger.info('Including band-gap in BS plot')
                yval[i+4] += yval[i][0]
            else:
                module_logger.info('Including band-gap in BS plot')
                yval[i+2] += yval[i][0]
            rmix.append(i)
    yval = np.delete(yval, rmix, 0)
    xval = np.delete(xval, rmix, 0)

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

    # plot vertical lines at special symmetry points if these are known
    if xticks:
        [ax.axvline(t, color='k', lw=1.0) for t in xticks]

    # plot reference Ek points with markers if given
#    if scatterpts is not None:
#        if isinstance(scatterpts, list):
#            _Ek = np.stack(scatterpts).transpose()
#        else:
#            _Ek = scatterpts.transpose()
#        ax.plot(_Ek[0], _Ek[1], color=colEkpts, marker='o', ls='', lw='1',
#                markersize=kwargs.get('markersize', 7))

    # set limits at the end, to make sure no artist tries to expand
    ax.set_ylim(ylim)
    ax.set_xlim(xlim)
    if title:
        ax.set_title(title, fontsize=16)
    if ylabels:
        ax.legend(legenditems, ylab, fontsize=14, loc=kwargs.get('legendloc', 0))
    fig.savefig(plotname+'.pdf')
    if kwargs.get('returnfigure', False):
        return fig
    else:
        plt.close('all')


class Plotter(object):
    """
    This class plots the bandstructure contained in 'data' to a file 
    named 'filename'. Energy range, and figure size may be controlled by
    'Erange' and 'figsize' respectively.
    'data' is a dictionary {'bands':values, 'kLines':values}; filename is a string.
    'refEkpts' and 'refBands' can be plotted, if supplied, but
    note that refBands must have the same number of k-points as data['bands']
    'refEkpts' is a list of tupples....
    'col' and 'colref' are used for data and ref* respectively.
    'data' bands may be plotted with cycling colours too (cycle_colors=True).
    """

    def __init__(self, data=None, filename=None,
                 Erange=[-13, +13], krange=None, figsize=(6, 7), log=logging.getLogger(__name__),
                 refEkpts=None, refBands=None, col='darkred', withmarkers=False, 
                 colref='blue', cycle_colors=False):
        """
        """
        self.data = data or {}
        self.filename = filename
        self.Erange = Erange
        self.krange = krange
        self.figsize = figsize
        self.refEkpts = refEkpts
        self.refBands = refBands
        self.log = log
        self.col = col
        self.withmarkers = withmarkers
        self.colref = colref
        self.cycle_colors = cycle_colors

    def plot(self, *args, **kwargs):
        """ 
        This method attempt to plot and save a figure of the bandstructure contained in self.data.
        self.data may be initialised at self.__init__() and the 'bands' and 'kLines' fields of data
        may be independently updated. This allows one to call plot() without any arguments.
        Alternatively, one may pass data explicitely using data = {'bands':values, 'kLines':values} 
        where 'bands' values are the E-k dispersion, and 'kLines' are the labels for 
        points of high symmetry.
        plot() can be called also with two positional arguments: bands,kLines
        or one positional arguments: data, or two key-value pairs: bands=..., kLines=...
        """
        if kwargs and 'filename' in kwargs:
            self.filename = kwargs['filename']

        if self.filename is None or not self.filename:
            self.log.critical('No filename specified for bandstrcture plot. Aborting execution.')
        else:
            self.log.debug('Plotting bandstructure to {0}'.format(self.filename))

        # here we allow plot() to be called with explicit data or
        # with explicit (bands,kLines), but retain the capability of
        # having self.data assigned during self.__init__() while its
        # key-values may be independently updated (as mutable object)
        # or by directly assigning Plotter.data = ... etc.
        if len(args) == 2:
            self.data['bandsPlt'] = args[0]
            self.data['kLinesPlt'] = args[1]
        if len(args) == 1:
            self.data = args[0]

        if kwargs:
            if 'data' in kwargs:
                self.data = kwargs['data']
            if all([k in kwargs for k in ('bands', 'kLines')]):
                self.data['bandsPlt'] = kwargs['bands']
                self.data['kLinesPlt'] = kwargs['kLines']
            if all([k in kwargs for k in ('bandsPlt', 'kLinesPlt')]):
                self.data['bandsPlt'] = kwargs['bandsPlt']
                self.data['kLinesPlt'] = kwargs['kLinesPlt']

        try:
            bands = self.data['bandsPlt']
            kLines = self.data['kLinesPlt']
        except KeyError:
            try:
                bands = self.data['bands']
                kLines = self.data['kLines']
            except:
                self.log.critical('Plotter {0} has wrongly assigned data field'.format(self))

        self.fig = plotBS(bands, kLines, Erange=self.Erange, krange=self.krange,
                        figsize=self.figsize,
                        refEkpts=self.refEkpts, refBands=self.refBands,
                        col=self.col, withmarkers=self.withmarkers, 
                        colref=self.colref, cycle_colors=self.cycle_colors,
                        log=self.log)
        self.fig.savefig(self.filename, bbox_inches='tight', pad_inches=0.01)
        plt.close()

        self.output = None
        return self.output


    def __call__(self, *args, **kwargs):
        self.plot(*args, **kwargs)

