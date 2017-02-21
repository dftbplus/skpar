import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from skopt.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skopt.dftbutils.queryDFTB import get_effmasses, get_special_Ek
from skopt.dftbutils.plot import plotBS

def get_model_data (src, dst, key, *args, **kwargs):
    """Get data from file and put it in a dictionary under a given key.

    Use numpy.loadtxt to get the data from `src` file and 
    write the data to `dst` dictionary under `key`. No interpretation or
    manipulation of the data is done.

    May be load arguments could be supported in the future, but 
    currently the optional positional and keyword arguments are ignored.
    """
    assert isinstance(src, str), \
        "src must be a filename string, but is {} instead.".format(type(src))
    assert isinstance(key, str), \
        "key must be a string naming the data, but is {} instead.".format(type(key))
    #logger.debug("Getting model data from {}:".format(src))
    data = np.loadtxt(src)
    #logger.debug(data)
    dst[key] = data

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
