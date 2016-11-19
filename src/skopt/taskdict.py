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


taskdict = {
        'get_dftb': get_dftb, 
        'get_meff': get_meff
        }
