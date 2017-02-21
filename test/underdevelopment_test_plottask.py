import unittest
import logging
import yaml
import os
from pprint import pprint, pformat
from os.path import abspath, normpath, expanduser
from os.path import join as joinpath
import numpy as np
import numpy.testing as nptest
from subprocess import CalledProcessError
from skopt.core.tasks import SetTask, RunTask, GetTask, set_tasks
from skopt.core.parameters import Parameter
from skopt.core.query import Query
from skopt.core.taskdict import gettaskdict

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

class ParsePlotTaskTest(unittest.TestCase):
    """Check if we can create and execute tasks."""

    yamldata="""
        tasks:
            #- set: [parfile, workdir, optional_arguments]
            #- run: [exe, workdir, arguments] 
            #- get: [func, source, destination, optional_arguments]
            #- plot: [func, plotname, abscissa, objectives, optional_arguments]
            - plot: [plotBS, 'bs-Si', [(bands, Si-bs)], k-Vector)
        """
    def test_parsetask(self):
        """Can we parse task declaration successfully"""
        Query.flush_modelsdb()
        spec = yaml.load(self.yamldata)['tasks']
        tasklist = []
        for tt in spec:
            # we should be getting 1 dict entry only!
            (tasktype, args), = tt.items()
            if tasktype.lower() == 'set':
                tasklist.append(SetTask(*args, logger=logger))
            if tasktype.lower() == 'run':
                tasklist.append(RunTask(*args, logger=logger))
            if tasktype.lower() == 'get':
                func = gettaskdict[args[0]]
                args[0] = func
                tasklist.append(GetTask(*args, logger=logger))
        self.assertTrue(isinstance(tasklist[0], SetTask))
        fun = ['get_dftbp_data', 'get_dftbp_data', 'get_dftbp_meff']
        cmd = ['skgen', 'bs_dftb', 'bs_dftb']
        wd  = ['skf', 'Si', 'SiO2']
        for ii, tt in enumerate(tasklist[1:4]):
            self.assertTrue(isinstance(tt, RunTask))
            self.assertListEqual(tt.cmd, [cmd[ii]])
            self.assertEqual(tt.wd, abspath(expanduser(wd[ii])))
        src = ['Si', 'SiO2', 'Si/bs']
        dst = ['Si', 'SiO2', 'Si']
        for ii, tt in enumerate(tasklist[4:]):
            self.assertTrue(isinstance(tt, GetTask))
            self.assertTrue(fun[ii], tt.func.__name__)
            self.assertEqual(src[ii], tt.src_name)
            self.assertEqual(dst[ii], tt.dst_name)


