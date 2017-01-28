import numpy as np
from skopt.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skopt.dftbutils.queryDFTB import get_effmasses, get_special_Ek

def get_model_data (src, dst, key, *args, **kwargs):
    """Get data from file and put it in a dictionary under a given key.

    Use numpy.loadtxt to get the data from `src` file and 
    write the data to `dst` dictionary under `key`. No interpretation or
    manipulation of the data is done.

    May be load arguemnts could be supported in the future, but 
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

gettaskdict = {
        'get_model_data': get_model_data,
        'get_dftbp_data': get_dftbp_data,
        'get_dftbp_bs'  : get_bandstructure,
        'get_dftbp_meff': get_effmasses,
        'get_dftbp_Ek'  : get_special_Ek,
        }
