import logging

def preconditionEkPlt_FCC(bands,kLines,kLinesDict):
    """
    Take bands, kLines and kLinesDict as input, and return:
        * bandsPlt less one for the equivalent k-points, e.g. U,K in FCC
    """
    import numpy as np
    nU = kLinesDict['U'][0]
    bandsPlt = np.delete(bands,nU,0)
    kLinesPlt = [k for k in kLines if k[0]!='U']
    for i,k in enumerate(kLinesPlt):
        if k[0] == 'K':
            kLinesPlt[i] = ('U,K',kLinesPlt[i][1])
    return bandsPlt,kLinesPlt

def preconditionEkPlt_TET(bands,kLines,kLinesDict):
    """
    Take bands, kLines and kLinesDict as input, and return:
        * bandsPlt less one for the equivalent k-points, 
        * update labels accordingly
    This preconditioning assumes the standard k-lines:
    Gamma--X--M--Gamma--Z--R--A--Z|X--R|M--A
    """
    import numpy as np
    nk = []
    nk.append(kLinesDict['X'][1]) # find the second appearance of X
    nk.append(kLinesDict['M'][1]) # find the second appearance of M
    bandsPlt = np.delete(bands,nk,0)
    
    kLinesPlt = []
    for i,k in enumerate(kLines):
        if i>0:
            kprec = kLines[i-1]
        if k[0] not in ['X','M']:
            if k[0] == 'Z' and kLines[i+1][0] == 'X':
                kLinesPlt.append(('Z|X',k[1]))
            elif k[0] == 'R' and kLines[i+1][0] == 'M':
                kLinesPlt.append(('R|M',k[1]-1)) # note the -1
            elif i == len(kLines)-1:
                kLinesPlt.append(('A',k[1]-2)) # note the -2
            else:
                kLinesPlt.append(k)
        else:
            if k[0] == 'X' and kprec[0] != 'Z':
                kLinesPlt.append(k)
            if k[0] == 'M' and kprec[0] != 'R':
                kLinesPlt.append(k)
    return bandsPlt,kLinesPlt


def plotBS (bands,kLines=None,Erange=[-13,13], refEkpts=None, refBands=None,
            col='darkred', colref='blue', cycle_colors=False,log=logging.getLogger('__name__'), **kwargs):
    """
    Plot the bands supplied to bands argument, along the k-lines in the kLines argument.
    Note that kLines is a list of tupples of the form (label_string,index_integer)
    Optionally specify refEkPts (e.g. a reference band-structure).
    Optionally specify the energy range Erange (defaults to [-13,13]) and figure size (dflt: 6x7)
    Optionally specify whether different colours should be used for each band (default True).
    Return a figure.
    """
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.ticker import AutoMinorLocator
    import numpy as np
    matplotlib.rcParams.update({'font.size': kwargs.get('fontsize',20), 'font.family': 'sans'})
    plt.rc('lines', linewidth=2)
    plt.rc('axes', color_cycle=['Red','Green','Blue','DarkBlue','LightBlue','Purple','Cyan','Olive','Maroon'])
    
    nk,nE = bands.shape

    # get a figure object with the desired figures size
    fig,ax = plt.subplots(figsize=kwargs.get('figsize',(6,7)))
    # set axis labels and ranges
    ax.set_xlabel('$\mathbf{k}$-vector')
    ax.set_ylabel('Energy (eV)')
    ax.set_xlim([0,nk-1])
    ax.set_ylim(Erange)
    # set ticks; ideally kLines will be obtained in advance from querying dftb_pin.hsd
    if kLines is not None:
        kTicks  = [k[1] for k in kLines]
        kLabels = [k[0] for k in kLines]
        ax.set_xticks(kTicks)
        ax.set_xticklabels(kLabels)
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    # plot the bands
    xx = xrange(nk)
    yy = np.transpose([bands[:,i] for i in xrange(nE)])
    # plot the bands
    if cycle_colors:
        ax.plot(xx,yy)
    else:
        ax.plot(xx,yy,color=col)
    # plot vertical lines at special symmetry points if these are known
    if kLines is not None:
        [plt.axvline(x=k,color='k') for k in kTicks]
    # plot reference Ek points with markers if given
    if refEkpts is not None:
        xx0 = np.transpose(refEk)[0]
        yy0 = np.transpose(refEk)[1]
        ax.plot(xx0,yy0,color=colref,marker='o',ls='*',lw='2',markersize=8)
    # TODO:
    # plot reference bands if full band-structure given as reference:
    # the condition here is that these must be along the same k-lines and same number of k-points
    # and that there are the same number nE for each nk; note that this latter condition is
    # relaxed above, for the refEkpts.
    # Note that if we want to permit different nk, then we cannot plot k-pt index on the x-axis.
    # we have to scale by actual length of the k-vector and plot that.... too sophisticated for the moment.
    if refBands is not None:
        if refBands.shape != bands.shape:
            log.warning('Ignoring refBands since refBands.shape != Bands. Cannot handle different k-pts in refBands.')
        else:
            yy0 = np.transpose([refBands[:,i] for i in xrange(nE)])
            ax.plot(xx,yy0,color=colRef)
    return fig





class PlotterBS(object):
    """
    """
    def __init__(self, data=None, filename=None, refBS=None, 
                 preconditioner=None, Erange=[-13,+13], figsize=(6,7), log=logging.getLogger(__name__)):
        """
        """
        self.filename = filename
        self.preconditioner = preconditioner
        self.Erange = Erange
        self.figsize = figsize
        self.refBS = refBS
        self.log = log
    

    def plot(self, filename=None):
        """
        """
        import matplotlib.pyplot as plt
        self.bands  = self.data['bands']
        self.kLines = self.data['kLines']
        self.kLinesDict = self.data['kLinesDict']
        if self.preconditioner is not None:
            self.bandsPlt, self.kLinesPlt = self.preconditioner(self.bands, self.kLines, self.kLinesDict)
        else: 
            self.bandsPlt, self.kLinesPlt = self.bands, self.kLines

        # now try hard to see if we can save the figure
        if filename is not None:
            # priority to arguments supplied with call
            self.filename = filename
        else:
            if self.filename is None:
                # if no filename in the call, and none initialized upon instantiation
                # check in the data - there should be a name that may be 
                # continuously updated from the caller
                try:
                    self.filename = self.data['plotBSfilename']
                except KeyError:
                    pass # self.filename remains unassigned and figure is not saved
        self.fig = plotBS(self.bandsPlt,self.kLinesPlt,self.Erange,refBS=self.refBS, figsize=self.figsize)
        if self.filename is not None:
            self.fig.savefig(self.filename, bbox_inches='tight',pad_inches=0.01)
        plt.close()

    def execute(self, *args, **kwargs):
        self.log.debug("Plotting bandstructure to {0}".format(self.filename))
        self.plot(*args, **kwargs)
        self.output = None
        return self.output

    def __call__(self):
        import sys
        if self.filename is None or not self.filename:
            self.log.critical('No filename specified for bandstrcture plot. Aborting execution.')
            sys.exit(0)
        else:
            self.execute()
