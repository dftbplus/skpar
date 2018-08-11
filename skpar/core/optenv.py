import logging
import os, sys, subprocess
from os.path import abspath, normpath, expanduser
from os.path import join as joinpath
from os.path import split as splitpath
import numpy as np
from subprocess import STDOUT
from pprint import pprint, pformat
from skpar.core.query import Query
from skpar.core.utils import get_logger


class ObjEnv(object):
    """Optimisation environment settings
    """
    def __init__(self, **kwargs):
        configuration = {
                workdroot: , 
                templaatedir: , 
                keepworkdirs: , 
                }

        parallel = {
                nmpip: ,
                nompt: ,
                }
        parameters = {
                }

        loggers
        
