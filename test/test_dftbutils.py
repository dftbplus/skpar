import unittest
import logging
import yaml
import os
from os.path import normpath, expanduser
import numpy as np
import numpy.testing as nptest
from skopt.tasks import GetTask
from subprocess import CalledProcessError
from skopt.taskdict import gettaskdict
from dftbutils.queryDFTB import DetailedOut, get_dftbp_data

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)


class DetailedOutTest(unittest.TestCase):
    """Check if we can read dftb+ detailed.out."""

    ref_scc = {
            "Ef": -3.2356,
            "Eband": -567.0004,
            "Ets":  0.0000,
            "Ebf": -567.0004,
            "E0K": -567.0004,
            "Eh0": -510.7031,
            "Escc":  0.1859,
            "Eel": -510.5172,
            "Erep":   0.0000,
            "Etot": -510.5172,
            "Emermin": -510.5172,
            #
            "nei": 32.0, 
            "neo": 32.0,
            #
            "converged": True,
            "withSOC": False}

    ref_scc_soc = {
            "Ef": -6.6732,
            "Eband": -100.4265,
            "Ets":  0.0000,
            "Ebf": -100.4265,
            "E0K": -100.4265,
            "Eh0": -84.3758,
            "Escc":  0.0330,
            "Els": -0.0004,
            "Eel": -84.3432,
            "Erep":   0.0000,
            "Etot": -84.3432,
            "Emermin": -84.3432,
            #
            "nei": 8.0, 
            "neo": 8.0,
            #
            "converged": True,
            "withSOC": True}

    ref_bs = {
            "Ef": 0.9931,
            "Eband": -563.7753,
            "Ets":  0.0000,
            "Ebf": -563.7753,
            "E0K": -563.7753,
            "Eh0": -507.4327,
            "Escc":  0.1756,
            "Eel": -507.2571,
            "Erep":   0.0000,
            "Etot": -507.2571,
            "Emermin": -507.2571,
            #
            "nei": 32.0, 
            "neo": 32.0,
            #
            "converged": False,
            "withSOC": False}

    # Electronic structure calculations (no atom relaxation)
    # SCC calculation without SOC
    def test_scc_out(self):
        src = 'test_dftbutils/scc/detailed.out'
        dst = DetailedOut.fromfile(src)
        self.assertDictEqual(dst, self.ref_scc)

    # SCC calculation with SOC
    def test_scc_out_withsoc(self):
        src = 'test_dftbutils/scc_soc/detailed.out'
        dst = DetailedOut.fromfile(src)
        self.assertDictEqual(dst, self.ref_scc_soc)

    # BS  calculation (not converged due to maxiscc=1)
    def test_bs_out(self):
        src = 'test_dftbutils/bs/detailed.out'
        dst = DetailedOut.fromfile(src)
        self.assertDictEqual(dst, self.ref_bs)

    def test_get_dftbp_data(self):
        dst = {}
        # src is file, including directory
        src = 'test_dftbutils/scc/detailed.out'
        get_dftbp_data(src, dst)
        self.assertDictEqual(dst, self.ref_scc)
        # src is a directory
        src = 'test_dftbutils/bs'
        get_dftbp_data(src, dst)
        # dictionary should be updated with new values, but same keys
        self.assertDictEqual(dst, self.ref_bs)
        # src is a file, but workdir is explicit
        src = 'detailed.out'
        wd = 'test_dftbutils/scc_soc'
        get_dftbp_data(src, dst, wd)
        self.assertDictEqual(dst, self.ref_scc_soc)


        


if __name__ == '__main__':
    unittest.main()

