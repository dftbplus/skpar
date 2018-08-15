"""
"""
import numpy as np
import logging
import os

def islistoflists(arg):
    """Return True if item is a list of lists.
    """
    claim = False
    if isinstance(arg, list):
        if isinstance(arg[0], list):
            claim = True
    return claim


def f2prange(rng):
    """Convert fortran range definition to a python one.
    
    Args:
        rng (2-sequence): [low, high] index range boundaries, 
            inclusive, counting starts from 1.
            
    Returns:
        2-tuple: (low-1, high)
    """
    lo, hi = rng
    msg = "Invalid range specification {}, {}.".format(lo, hi)\
        + " Range should be of two integers, both being >= 1."
    assert lo >= 1 and hi>=lo, msg
    return lo-1, hi

def get_ranges(data):
    """Return list of tuples ready to use as python ranges.

    Args:
        data (int, list of int, list of lists of int):
            A single index, a list of indexes, or a list of
            2-tuple range of indexes in Fortran convention,
            i.e. from low to high, counting from 1, and inclusive
    
    Return:
        list of lists of 2-tuple ranges, in Python convention -
        from 0, exclusive.
    """
    try:
        rngs = []
        for rng in data:
            try:
                lo, hi = rng
            except TypeError:
                lo, hi = rng, rng
            rngs.append(f2prange((lo, hi)))
    except TypeError:
        # data not iterable -> single index, convert to list of lists
        rngs = [f2prange((data,data))]
    return rngs

def configure_logger(name, filename='skpar.log', verbosity=logging.INFO):
    """Get parent logger: logging INFO on the console and DEBUG to file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # may need this if running within ipython notebook, to avoid duplicates
    logger.propagate = False
    # console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(verbosity)
    # file handler with full debug info
    if not os.name=='nt':
        fh = logging.FileHandler(filename, mode='w')
    else:
        # on windows using filehandler yields logging exceptions for utf-8 chars, e.g. Γ
        # using streamhandler removes the exception, but erroneous chars may end up in file.
        # for some reason the code page of the console is not taken in account by the
        # logger, and I cannot find solution to that.
        fh = logging.StreamHandler(open(filename, mode='w', encoding='utf-8'))
    fh.setLevel(logging.DEBUG)
    debug_filename = filename.split('.')
    debug_filename = '.'.join(debug_filename[:-1]+['debug']+[debug_filename[-1]])
    if not os.name=='nt':
        fhd = logging.FileHandler(debug_filename, mode='w')
    else:
        # on windows using filehandler yields logging exceptions for utf-8 chars, e.g. Γ
        # using streamhandler removes the exception, but erroneous chars may end up in file.
        # for some reason the code page of the console is not taken in account by the
        # logger, and I cannot find solution to that.
        fhd = logging.StreamHandler(open(debug_filename, mode='w', encoding='utf-8'))
    fh.setLevel(logging.INFO)
    fhd.setLevel(logging.DEBUG)
    # message formatting
    consformat = logging.Formatter('%(levelname)7s: %(message)s')
    fh.setFormatter(consformat)
    ch.setFormatter(consformat)
    fileformat = logging.Formatter('%(name)s - %(levelname)s: %(message)s')
    fhd.setFormatter(fileformat)
    # add the configured handlers
    logger.addHandler(fh)
    logger.addHandler(fhd)
    logger.addHandler(ch)
    return logger

def get_logger(name, filename=None, verbosity=logging.INFO):
    """Return a named logger with file and console handlers.

    Get a `name`-logger. Check if it is(has) a parent logger.
    If parent logger is not configured, configure it, and if a child logger
    is needed, return the child.
    The check for parent logger is based on `name`: a child if it contains '.',
    i.e. looking for 'parent.child' form of `name`.
    A parent logger is configured by defining a console handler at `verbosity`
    level, and a file handler at DEBUG level, writing to `filename`.
    """
    parent = name.split('.')[0]
    if filename is None:
        filename = parent+'.log'
    parent_logger = logging.getLogger(parent)
    if not parent_logger.handlers:
        configure_logger(parent, filename, verbosity)
    return logging.getLogger(name)

def normalise(a):
    """Normalise the given array so that sum of its elements yields 1.

    Args:
        a (array): input array

    Returns:
        a/norm (array): The norm is the sum of all elements across all dimensions.
    """
    norm = np.sum(np.asarray(a))
    return np.asarray(a)/norm

def arr2s(aa, precision=3, suppress_small=True, max_line_width=75):
    """Helper for compact string representation of numpy arrays.
    """
    ss = np.array2string(aa, precision=precision, suppress_small=suppress_small,
            max_line_width=max_line_width)
    return ss

def is_monotonic(x):
    dx = np.diff(x)
    return np.all(dx <= 0) or np.all(dx >= 0)

def normaliseWeights(weights):
    """
    normalise weights so that their sum evaluates to 1
    """
    return np.asarray(weights)/np.sum(np.asarray(weights))

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
