"""
"""
import os
import numpy as np
import logging

def flatten (dd):
    """
    Take a dictionary or list of dictionaries/lists dd,
    and produce a lists of values corresponding, dropping the keys.
    """
    try: # assume current item is a dictionary; iterate over its items
        for key,val in dd.items():
            for nested_val in flatten(val):
                yield nested_val
    except AttributeError: # not a dictionary
        try: # assume current item is a list; iterate over its items
            for i,val in enumerate(dd):
                for nested_val in flatten(val):
                    yield nested_val
        except TypeError: # it is just a number then; return it
            yield dd

def flatten_two (d1, d2):
    """
    Take two dictionaries or lists of dictionaries/lists d1 and d2,
    and produce two lists of values corresponding to the keys/order in d1.
    d2 is optional.
    Assume that the keys of d1 are a subset of the keys of d2.
    Assume nesting, i.e. some of the items in d1 are dictionaries
    and some are lists, numpy arrays, or a non-sequence type.
    The assumption is again: nested dictionaries in d2 must have
    at least the keys of the corresponding nested dictionaries in d1,
    and the lists in d1 must be no shorter than the lists in d2.
    ...some assertions may help here...
    """
    try: # assume current item is a dictionary; iterate over its items
        for key, val in d1.items():
            for nested_val_1,nested_val_2 in flatten_two(val,d2[key]):
                yield nested_val_1, nested_val_2
    except AttributeError: # not a dictionary
        try: # assume current item is a list; iterate over its items
            for i, val in enumerate(d1):
                for nested_val_1, nested_val_2 in flatten_two(val,d2[i]):
                    yield nested_val_1, nested_val_2
        except TypeError: # it is just a number then; return it
# this fails if one number is native python number while
# the other is a numpy scalar
            #assert isinstance(d2,type(d1)), (
            #    '\n{0} \n and \n{1} \nare of different type '
            #    '\n{2} \n and \n{3}'
            #    '\nand cannot be flattened simultaneously.'.
            #    format(d2,d1,type(d2),type(d1)))
            assert not (hasattr(d1,'__iter__') or hasattr(d2,'__iter__')), (
                '\n\t{0}\n{1}' 
                '\n\tand'
                '\n\t{2}\n{3}' 
                '\n\tcannot be flattened simultaneously.'.
                format(type(d1),d1,type(d2),d2))
            yield d1, d2

def subpath (wd,*pathfragments):
    return os.path.join(wd,*pathfragments)


def is_monotonic(x):
    dx = np.diff(x)
    return np.all(dx <= 0) or np.all(dx >= 0)


def normalise(a):
    """Normalise the given array so that sum of its elements yields 1.

    Args:
        a (array): input array

    Returns:
        a/norm (array): The norm is the sum of all elements across all dimensions.
    """
    norm = np.sum(np.asarray(a))
    return np.asarray(a)/norm

def normaliseWeights(weights):
    """
    normalise weights so that their sum evaluates to 1
    """
    return np.asarray(weights)/np.sum(np.asarray(weights))

def setup_logger(name, filename, verbosity=logging.INFO):
    """Return a named logger with file and console handlers.

    Get a `name`-logger and define a console handler at INFO level,
    and a file handler at DEBUG level, writing to `filename`.
    """
    # set up logging
    # -------------------------------------------------------------------
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(verbosity)
    # file handler with full debug info
    fh = logging.FileHandler(filename)
    fh.setLevel(logging.DEBUG)
    # message formatting
    formatter = logging.Formatter('%(levelname)7s: %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def get_logger(logger=None):
    """
    One-liner to attempt and set a logger for an object.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    else:
        logger = logger
    return logger
    

if __name__ == "__main__":

    import numpy as np
    from collections import OrderedDict

    bands1 = np.array([[1., 2., 3.],[4., 5., 6.]])
    bands2 = np.array([[1.1,2.2,3.3],[4.4,5.5,6.6]])
    bands3 = np.array([[7,8,9],[10,11,12]])
    bands4 = np.array([[71,81,91],[10,101,102]])

    d1 = OrderedDict({ 'SKFgen':{},
            'Si':{'Egap':1.1, 'bands':bands1,},
            'SiO2':{'Egap':9.0, 'bands':bands3} })
    d2 = OrderedDict({  'SKFgen':{},
            'Si':{'Egap':1.12, 'Etot':300, 'bands':bands2,},
            'SiO2':{'Egap':8.9, 'Etot':900, 'bands':bands4} })
    print(list(flatten(d1)))
    print (d1)


    #for data in flatten(d1,d2):
    #    print data
    ref,calc = list(zip(*list(flatten_two(d1,d2))))
    print (ref)
    print (calc)

    d3 = OrderedDict({  'SKFgen':{},
            'Si':{'Egap':1.12, 'Etot':300, 'bands':1./3.,},
            'SiO2':{'Egap':8.9, 'Etot':900, 'bands':bands4} })
    # uncomment for assertion test
    # ref1,cal1 = zip(*list(flatten_two(d1,d3)))
