"""Test plotting functions."""
import unittest
import logging
import os
import numpy as np
from numpy.random import random
from skpar.dftbutils.queryDFTB import get_bandstructure
from skpar.dftbutils.plot import plot_bs, magic_plot_bs
from skpar.core.database import Database
from skpar.core.plot import skparplot
np.set_printoptions(precision=2, suppress=True)

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
LOGGER = logging.getLogger(__name__)

def init_test_plot_bs(basename):
    """Some common initialisation for the test_plot_bs_*"""
    twd = '_workdir/test_plot'
    filename = os.path.join(twd, basename)
    if os.path.exists(filename):
        os.remove(filename)
    else:
        os.makedirs(twd, exist_ok=True)
    bsdata = np.loadtxt("reference_data/fakebands.dat", unpack=True)
    return filename, bsdata

class BandstructurePlotTest(unittest.TestCase):
    """Test bandstructure plotting back-end and magic"""

    def test_plot_bs_1(self):
        """Can we plot a bandsturcture, given as a x, and y array?"""
        filename, bsdata = init_test_plot_bs('test_plot_bs_1.pdf')
        xx1 = bsdata[0]
        yy1 = bsdata[1:]
        xtl = None
        fig, _ax = plot_bs(xx1, yy1, ylim=(-2.5, 2.5),
                           xticklabels=xtl, linelabels=['ref', 'model'],
                           title='Test 1 array', xlabel=None)
        fig.savefig(filename)
        self.assertTrue(os.path.exists(filename))

    def test_plot_bs_2(self):
        """Can we plot a two bandsturctures with shared k-points?"""
        filename, bsdata = init_test_plot_bs('test_plot_bs_2.pdf')
        xx1 = bsdata[0]
        yy1 = bsdata[1:]
        jitter = .1 * (0.5 - random(yy1.shape))
        yy2 = yy1 + jitter
        xtl = [(1, 'X'), (6, 'Gamma'), (10, 'L')]
        plot_bs(xx1, [yy1, yy2], ylim=(-2.5, 2.5),
                xticklabels=xtl, linelabels=['ref', 'model'],
                title='Test 2 array common X', xlabel=None,
                filename=filename)
        self.assertTrue(os.path.exists(filename))

    def test_plot_bs_3(self):
        """Can we plot a two bandsturctures with 2 sets of k-points?"""
        filename, bsdata = init_test_plot_bs('test_plot_bs_3.pdf')
        xx1 = bsdata[0]
        yy1 = bsdata[1:]
        jitter = .1 * (0.5 - random(yy1.shape))
        yy2 = yy1 + jitter
        xtl = [(1, 'X'), (6, 'Gamma'), (11, 'L')]
        plot_bs([xx1, xx1], [yy1, yy2], ylim=(-2.5, 2.5),
                xticklabels=xtl, linelabels=['ref', 'model'],
                title='Test 2 bands 2 kpts', xlabel=None,
                filename=filename)
        self.assertTrue(os.path.exists(filename))

    def test_plot_bs_4(self):
        """Can we plot a two bandsturctures with 2 different of k-points?"""
        filename, bsdata = init_test_plot_bs('test_plot_bs_4.pdf')
        xx1 = bsdata[0]
        yy1 = bsdata[1:]
        j = 6
        jitter = .1 * (0.5 - random(yy1[:j, :8].shape))
        yy2 = yy1[:j, :8] + jitter
        xx2 = xx1[:8]
        xtl = [(1, 'X'), (6, 'Gamma'), (8, 'K'), (11, 'L')]
        plot_bs([xx1, xx2], [yy1, yy2], ylim=(-2.5, 2.5),
                xticklabels=xtl, linelabels=['ref', 'model'],
                title='Test 2 bands 2 (different) kpts', xlabel=None,
                filename=filename)
        self.assertTrue(os.path.exists(filename))

    def test_magic_plot_bs_1(self):
        """Can we call the magic without the need for magic?"""
        filename, bsdata = init_test_plot_bs('test_magic_plot_bs_1.pdf')
        xx1 = bsdata[0]
        yy1 = bsdata[1:]
        jitter = .1 * (0.5 - random(yy1.shape))
        yy2 = yy1 + jitter
        xx2 = xx1
        xtl = [(1, 'X'), (6, 'Gamma'), (8, 'K'), (11, 'L')]
        magic_plot_bs([xx1, xx2], [yy1, yy2], filename=filename,
                      ylim=(-2.5, 2.5), xticklabels=xtl,
                      linelabels=['ref', 'model'],
                      title='Test magic without gap', xlabel=None)
        self.assertTrue(os.path.exists(filename))

    def test_magic_plot_bs_2(self):
        """Can we call the magic with gap?"""
        filename, bsdata = init_test_plot_bs('test_magic_plot_bs_2.pdf')
        xx1 = bsdata[0]
        yy1 = bsdata[1:]
        jitter = .1 * (0.5 - random(yy1.shape))
        yy2 = yy1 + jitter
        xx2 = xx1
        xtl = [(1, 'X'), (6, 'Gamma'), (8, 'K'), (11, 'L')]
        eg1 = np.atleast_1d(0.3)
        eg2 = np.atleast_1d(0.4)
        magic_plot_bs([xx1, xx2, xx1, xx2],
                      [eg1, eg2, yy1[:4], yy2[:4], yy1[4:], yy2[4:]],
                      filename=filename, ylim=(-2.5, 2.5),
                      colors=['b', 'darkred', 'b', 'darkred'],
                      xticklabels=xtl, linelabels=['ref', 'model'],
                      title='Test magic 2 Eg Eg VB VB CB CB', xlabel=None)
        self.assertTrue(os.path.exists(filename))

    def test_magic_plot_bs_3(self):
        """Can we call the magic with gap (alternative yval order)?"""
        filename, bsdata = init_test_plot_bs('test_magic_plot_bs_3.pdf')
        xx1 = bsdata[0]
        yy1 = bsdata[1:]
        jitter = .1 * (0.5 - random(yy1.shape))
        yy2 = yy1 + jitter
        xx2 = xx1
        xtl = [(1, 'X'), (6, 'Gamma'), (8, 'K'), (11, 'L')]
        eg1 = np.atleast_1d(0.3)
        eg2 = np.atleast_1d(0.4)
        magic_plot_bs([xx1, xx1, xx2, xx2],
                      [eg1, yy1[:4], yy1[4:], eg2, yy2[:4], yy2[4:]],
                      filename=filename, ylim=(-2.5, 2.5),
                      colors=['b', 'b', 'r', 'r'], xticklabels=xtl,
                      linelabels=['ref', None, 'model', None],
                      title='Test magic 3 Eg VB CB Eg VB CB', xlabel=None)
        self.assertTrue(os.path.exists(filename))

class GenericPlotTaskTest(unittest.TestCase):
    """Test generic plot-task from tasksdict for  1D and 2D plots"""

    def test_skparplot(self):
        """Can we plot a band-structure objectives?"""
        env = {}
        database = Database()
        latticeinfo = {'type': 'FCC', 'param': 5.4315}
        model = 'Si.bs'
        filename = '_workdir/test_plot/bs1.pdf'
        get_bandstructure(env, database, 'test_dftbutils/Si/bs/', model,
                          latticeinfo=latticeinfo)
        modeldb = database.get(model)
        bands = modeldb['bands']
        eps = 0.25
        jitter = eps * (0.5 - random(bands.shape))
        altbands = bands + jitter
        if os.path.exists(filename):
            os.remove(filename)
        else:
            os.makedirs('_workdir/test_plot', exist_ok=True)
        skparplot(modeldb['kvector'], [altbands, bands],
                  filename=filename, xticklabels=modeldb['kticklabels'],
                  xlabel='wave-vector', ylabel='Energy, eV',
                  linelabels=['ref', 'model'], ylim=(-13, 6))
        self.assertTrue(os.path.exists(filename))

if __name__ == '__main__':
    unittest.main()
