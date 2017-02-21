import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import logging


def plotBS(bands_in, kvec, Erange=[-13, 13], krange=None, figsize=(6, 7),\
           col='darkred', withmarkers=False, Ekscatter=None, colEkpts='blue',\
           kLabels=None, **kwargs):
    """
    """
    matplotlib.rcParams.update({'font.size': kwargs.get('fontsize', 20),\
                                'font.family': kwargs.get('fontfamily', 'sans')})
    plt.rc('lines', linewidth=2)
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlabel('$\mathbf{k}$-vector')
    ax.set_ylabel('Energy (eV)')
    # Deal with bands input: make bands and col lists, even if they are not
    nE, nk = [], []
    if isinstance(bands_in, list):
        bands = bands_in
    else:
        bands = [bands_in, ]
    for item in bands:
        nE.append(item.shape[0])
        nk.append(item.shape[1])
    for item in nk:
        assert item==len(kvec), (item, len(kvec))
    if isinstance(col, list):
        assert len(col)==len(bands)
    else:
        col = [col,]
    print (len(bands), len(col))
    # plot the bands
    for b, c in zip(bands, col):
        if withmarkers:
            ax.plot(kvec, b.transpose(), color=c, marker='o', markersize=kwargs.get('markersize', 4))
        else:
            ax.plot(kvec, b.transpose(), color=c)
    # set k-labels and v-lines at corresponding ticks
    if kLabels is not None:
        ticks, labels  = zip(*kLabels)
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
    else:
        ticks = None
        labels = None
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    # plot vertical lines at special symmetry points if these are known
    if ticks:
        [ax.axvline(x=k, color='k', lw=0.5) for k in ticks]
    # plot reference Ek points with markers if given
    if Ekscatter is not None:
        if isinstance(Ekscatter, list):
            _Ek = np.stack(Ekscatter).transpose()
        else:
            _Ek = Ekscatter.transpose()
        ax.plot(_Ek[0], _Ek[1], color=colEkpts, marker='o', ls='', lw='1',
                markersize=kwargs.get('markersize', 7))
    # set limits at the end, to make sure no artist tries to expand
    ax.set_ylim(Erange)
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

