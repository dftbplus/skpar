import unittest
import logging
import numpy as np
import numpy.testing as nptest
from numpy.random import random
import os
from os.path import abspath, normpath, expanduser
from numpy import pi, sqrt
from fractions import Fraction
import logging
from skpar.dftbutils.lattice import Lattice
from skpar.dftbutils.queryDFTB import get_bandstructure
from skpar.dftbutils.querykLines import get_klines, get_kvec_abscissa
from skpar.core.taskdict import plot_objvs
from skpar.dftbutils.plot import plotBS
np.set_printoptions(precision=2, suppress=True)

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

class GenericPlotTaskTest(unittest.TestCase):
    """Test generic plot-task from tasksdict for  1D and 2D plots"""

    def test_plot_bs(self):
        """Can we plot a band-structure?"""
        latticeinfo = {'type': 'FCC', 'param': 5.4315}
        DB = {}
        plotname = '_workdir/test_plot/bs1.pdf'
        get_bandstructure('.', 'test_dftbutils/Si/bs/', DB,
                          latticeinfo={'type': 'FCC', 'param': 5.4315})
        bands = DB['bands']
        eps = 0.25
        jitter = eps * (0.5 - random(bands.shape))
        altbands = bands + jitter
        if os.path.exists(plotname):
            os.remove(plotname)
        else:
            os.makedirs('_workdir/test_plot', exist_ok=True)
        plot_objvs('_workdir/test_plot/bs1', DB['kvector'], [altbands, bands], 
                xticklabels=DB['kticklabels'],
                axeslabels=['wave-vector', 'Energy, eV'], 
                ylabels=['ref', 'model'], ylim=(-13, 6))
        self.assertTrue(os.path.exists(plotname))


if __name__ == '__main__':
    unittest.main()
