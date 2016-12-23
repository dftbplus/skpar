import numpy as np

def get_dftb(src, dest, wd=None):
    """fake function"""
    if wd is None:
        assert isinstance(src, str)
        wd = src
    # do mambo
    pass

def get_meff(src, dest, *args, **kwargs):
    """fake function with arguments"""
    pass

def get_model_data (src, dst, key, *args, **kwargs):
    assert isinstance(src, str), \
        "src must be a filename string, but is {} instead.".format(type(src))
    assert isinstance(key, str), \
        "key must be a string naming the data, but is {} instead.".format(type(key))
    #logger.debug("Getting model data from {}:".format(src))
    data = np.loadtxt(src)
    #logger.debug(data)
    dst[key] = data


gettaskdict = {
        'get_dftb': get_dftb, 
        'get_meff': get_meff, 
        'get_model_data': get_model_data
        }
