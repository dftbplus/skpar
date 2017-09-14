"""
"""
import numpy as np
import logging

def configure_logger(name, filename=None, verbosity=logging.INFO):
    """Get parent logger: logging INFO on the console and DEBUG to file.
    """
    if filename is None:
        filename = name+'.debug.log'
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # may need this if running within ipython notebook, to avoid duplicates
    logger.propagate = False
    # console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(verbosity)
    # file handler with full debug info
    fh = logging.FileHandler(filename, mode='w')
    fh.setLevel(logging.DEBUG)
    # message formatting
    fileformat = logging.Formatter('%(name)s - %(levelname)s: %(message)s')
    consformat = logging.Formatter('%(levelname)7s: %(message)s')
    fh.setFormatter(fileformat)
    ch.setFormatter(consformat)
    # add the configured handlers
    logger.addHandler(fh)
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
        filename = parent+'.debug.log'
    parent_logger = logging.getLogger(parent)
    if not parent_logger.handlers:
        configure_logger(parent, filename, verbosity)
    return logging.getLogger(name)
