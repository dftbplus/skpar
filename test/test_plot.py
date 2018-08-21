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
from skpar.core.taskdict import skparplot
from skpar.dftbutils.plot import plot_bs, magic_plot_bs
np.set_printoptions(precision=2, suppress=True)

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

def init_test_plot_bs(fn):
    """Some common initialisation for the test_plot_bs_*"""
    twd = '_workdir/test_plot'
    filename = os.path.join(twd, fn)
    if os.path.exists(fn):
        os.remove(fn)
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
        fig, ax = plot_bs(xx1, yy1, ylim=(-2.5, 2.5), 
                xticklabels=xtl, linelabels=['ref', 'model'],
                title='Test 1 array', xlabel=None)
        fig.savefig(filename)

    def test_plot_bs_2(self):
        """Can we plot a two bandsturctures with shared k-points?"""
        filename, bsdata = init_test_plot_bs('test_plot_bs_2.pdf')
        xx1 = bsdata[0]
        yy1 = bsdata[1:]
        jitter = .1 * (0.5 - random(yy1.shape))
        yy2 = yy1 + jitter
        xtl = [(1, 'X'), (6, 'Gamma'), (10, 'L')]
        fig, ax = plot_bs(xx1, [yy1, yy2], ylim=(-2.5, 2.5), 
                xticklabels=xtl, linelabels=['ref', 'model'],
                title='Test 2 array common X', xlabel=None,
                filename=filename)

    def test_plot_bs_3(self):
        """Can we plot a two bandsturctures with 2 sets of k-points?"""
        filename, bsdata = init_test_plot_bs('test_plot_bs_3.pdf')
        xx1 = bsdata[0]
        yy1 = bsdata[1:]
        jitter = .1 * (0.5 - random(yy1.shape))
        yy2 = yy1 + jitter
        xtl = [(1, 'X'), (6, 'Gamma'), (11, 'L')]
        fig, ax = plot_bs([xx1, xx1], [yy1, yy2], ylim=(-2.5, 2.5), 
                xticklabels=xtl, linelabels=['ref', 'model'],
                title='Test 2 bands 2 kpts', xlabel=None,
                filename=filename)

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
        fig, ax = plot_bs([xx1, xx2], [yy1, yy2], ylim=(-2.5, 2.5), 
                xticklabels=xtl, linelabels=['ref', 'model'],
                title='Test 2 bands 2 (different) kpts', xlabel=None,
                filename=filename)

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
                ylim=(-2.5, 2.5), 
                xticklabels=xtl, linelabels=['ref', 'model'],
                title='Test magic without gap', xlabel=None)

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
                filename=filename,
                ylim=(-2.5, 2.5), colors = ['b','darkred','b','darkred'],
                xticklabels=xtl, linelabels=['ref', 'model'],
                title='Test magic 2 Eg Eg VB VB CB CB', xlabel=None)

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
                filename=filename,
                ylim=(-2.5, 2.5), colors=['b','b','r','r'],
                xticklabels=xtl, linelabels=['ref', None, 'model', None],
                title='Test magic 3 Eg VB CB Eg VB CB', xlabel=None)

class GenericPlotTaskTest(unittest.TestCase):
    """Test generic plot-task from tasksdict for  1D and 2D plots"""

    def test_skparplot(self):
        """Can we plot a band-structure objectives?"""
        Query.flush_modelsdb()
        env = {}
        database = {}
        latticeinfo = {'type': 'FCC', 'param': 5.4315}
        model = 'Si.bs'
        filename = '_workdir/test_plot/bs1.pdf'
        get_bandstructure(env, database, 'test_dftbutils/Si/bs/', model,
                          latticeinfo={'type': 'FCC', 'param': 5.4315})
        db = get_modeldb(model)
        bands = db['bands']
        eps = 0.25
        jitter = eps * (0.5 - random(bands.shape))
        altbands = bands + jitter
        if os.path.exists(filename):
            os.remove(filename)
        else:
            os.makedirs('_workdir/test_plot', exist_ok=True)
        skparplot(env, dabase, db['kvector'], [altbands, bands],
                filename=filename, xticklabels=db['kticklabels'],
                xlabel='wave-vector', ylabel='Energy, eV',
                linelabels=['ref', 'model'], ylim=(-13, 6))
        self.assertTrue(os.path.exists(filename))

if __name__ == '__main__':
    unittest.main()
