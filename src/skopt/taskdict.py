import numpy as np
from dftbp.queryDFTB import get_dftbp_data

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

def get_meff(src, dest, *args, **kwargs):
    """fake function with arguments"""
    pass

gettaskdict = {
        'get_model_data': get_model_data,
        'get_dftbp_data': get_dftbp_data,
        'get_meff': get_meff,
        }
