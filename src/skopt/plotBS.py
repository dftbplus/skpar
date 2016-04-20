import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import logging


def plotBS(bands, kLines=None, Erange=[-13, 13], krange=None, figsize=(6, 7), \
           refEkpts=None, refBands=None, \
           col='darkred', withmarkers=False, colref='blue', \
           cycle_colors=False, log=logging.getLogger('__name__'), **kwargs):
    """
    Plot the bands supplied to bands argument, along the k-lines in the kLines argument.
    Note that kLines is a list of tupples of the form (label_string,index_integer)
    Optionally specify refEkPts (e.g. a reference band-structure).
    Optionally specify the energy range Erange (defaults to [-13,13]) 
    and figure size (dflt: 6x7)
    Optionally specify whether different colours should be used for each 
    band (default True).
    Return a figure.
    """
    matplotlib.rcParams.update({'font.size': kwargs.get('fontsize', 20), \
                                'font.family': kwargs.get('fontfamily', 'sans')})
    plt.rc('lines', linewidth=2)
    color_cycle=['Red', 'Green', 'Blue', 'DarkBlue', \
                    'LightBlue', 'Purple', 'Cyan', 'Olive', 'Maroon']

    nk, nE = bands.shape

    # get a figure object with the desired figures size
    fig, ax = plt.subplots(figsize=figsize)
    ax.prop_cycle = color_cycle
    # set axis labels and ranges
    ax.set_xlabel('$\mathbf{k}$-vector')
    ax.set_ylabel('Energy (eV)')
    if krange is None:
        krange = [0, nk - 1]
    ax.set_ylim(Erange)
    ax.set_xlim(krange)
    # set ticks; ideally kLines will be obtained in advance from querying dftb_pin.hsd
    if kLines is not None:
        kTicks = [k[1] for k in kLines]
        kLabels = [k[0] for k in kLines]
        ax.set_xticks(kTicks)
        ax.set_xticklabels(kLabels)
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    # plot the bands
    xx = range(nk)
    yy = np.transpose([bands[:, i] for i in range(nE)])
    # plot the bands
    if cycle_colors:
        ax.plot(xx, yy)
    else:
        if withmarkers:
            ax.plot(xx, yy, color=col, marker='o', markersize=8)
        else:
            ax.plot(xx, yy, color=col)

    # plot vertical lines at special symmetry points if these are known
    if kLines is not None:
        [plt.axvline(x=k, color='k') for k in kTicks]
    # plot reference Ek points with markers if given
    if refEkpts is not None:
        xx0 = np.transpose(refEkpts)[0]
        yy0 = np.transpose(refEkpts)[1]
        ax.plot(xx0, yy0, color=colref, marker='o', ls='*', lw='2', markersize=8)
    # TODO:
    # plot reference bands if full band-structure given as reference:
    # the condition here is that these must be along the same k-lines and same 
    # number of k-points and that there are the same number nE for each nk;
    # note that this latter condition is relaxed above, for the refEkpts.
    # Note that if we want to permit different nk, then we cannot plot k-pt 
    # index on the x-axis.
    # we have to scale by actual length of the k-vector and plot that.... 
    # too sophisticated for the moment.
    if refBands is not None:
        if refBands.shape != bands.shape:
            log.warning('Ignoring refBands since refBands.shape != Bands.' + \
                        'Cannot handle different k-pts in refBands.')
        else:
            yy0 = np.transpose([refBands[:, i] for i in range(nE)])
            ax.plot(xx, yy0, color=colRef)
    ax.set_xlim(krange)
    return fig


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

