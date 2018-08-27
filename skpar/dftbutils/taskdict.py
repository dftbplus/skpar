"""
Provide mapping between task names available to user and actual functions.
"""
from skpar.core.utils import get_logger
from skpar.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skpar.dftbutils.queryDFTB import get_dftbp_evol
from skpar.dftbutils.queryDFTB import get_effmasses, get_special_Ek
from skpar.dftbutils.plot import magic_plot_bs

LOGGER = get_logger(__name__)

TASKDICT = {
    # obtain data from model evaluations
    'get_data': get_dftbp_data,
    'get_evol': get_dftbp_evol,
    'get_bs'  : get_bandstructure,
    'get_meff': get_effmasses,
    'get_Ek'  : get_special_Ek,
    # plot data
# this one is currently used via the wrapper of PlotTask in ../core/taskdict.py
    'plot_bs' : magic_plot_bs,
    }
