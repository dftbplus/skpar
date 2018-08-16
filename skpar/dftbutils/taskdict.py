"""
Provide mapping between task names available to user and actual functions.
"""
from skpar.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skpar.dftbutils.queryDFTB import get_dftbp_evol
from skpar.dftbutils.queryDFTB import get_effmasses, get_special_Ek
from skpar.dftbutils.plot import magic_plot_bs

TASKDICT = {
    # obtain data from model evaluations
    'get_dftbp_data': get_dftbp_data,
    'get_dftbp_evol': get_dftbp_evol,
    'get_dftbp_bs'  : get_bandstructure,
    'get_dftbp_meff': get_effmasses,
    'get_dftbp_Ek'  : get_special_Ek,
    # plot data
    'plot_bs' : magic_plot_bs,
    }
