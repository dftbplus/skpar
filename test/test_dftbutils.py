import unittest
import logging
import numpy as np
import numpy.testing as nptest
from dftbutils.queryDFTB import DetailedOut, BandsOut, Bandstructure
from dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from dftbutils import queryDFTB as dftb
from math import pi

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


class BandsOutTest(unittest.TestCase):
    """Check if we can read bands_tot.dat from dp_bands."""

    ff1 = 'reference_data/fakebands.dat'
    fake_bands = np.loadtxt(ff1)
    # eliminate column 1, which enumerates the kpoints
    fake_bands = fake_bands[:, 1:]
    fake_nk, fake_nb = fake_bands.shape

    ff2 = 'test_dftbutils/bs/bands_tot.dat'
    ref_bands = np.loadtxt(ff2)
    ref_bands = ref_bands[:, 1:]
    ref_nk, ref_nb = ref_bands.shape
    ref_ivbtop = int(len(ref_bands.shape[1]/2))
    ref_Ev = np.max(ref_bands[:, ref_ivbtop])
    ref_Ec = np.min(ref_bands[:, ref_ivbtop+1])
    ref_Eg = ref_Ec - ref_Ev
    ref_Ef = 0.9931

    def test_bands_out(self):
        """Can we get the 2D array corresponding to energies in bands_tot.dat?"""
        dst = BandsOut.fromfile(self.ff1)
        nptest.assert_array_almost_equal(dst['bands'], self.fake_bands)
        self.assertEqual(dst['nkpts'], self.fake_nk)
        self.assertEqual(dst['nbands'], self.fake_nb)

    def test_bandstructure(self):
        """Can we get the bandstructure and gap/cb/vb details?"""
        f1 = 'test_dftbutils/bs/detailed.out' 
        f2 = 'test_dftbutils/bs/bands_tot.dat' 
        data = Bandstructure.fromfiles(f1, f2)
        nptest.assert_array_almost_equal(data['bands'], self.ref_bands)
        self.assertEqual(data['nkpts'], self.ref_nk)
        self.assertEqual(data['nbands'], self.ref_nb)
        self.assertEqual(data['Ef'], self.ref_Ef)
        self.assertEqual(data['ivbtop'], self.ref_ivbtop)
        self.assertEqual(data['Egap'], self.ref_Eg)
        self.assertEqual(data['Ecb'], self.ref_Ec)
        self.assertEqual(data['Evb'], self.ref_Ev)

    def test_get_bandstructure_dirsrc(self):
        """Can we get the bandstructure and gap/cb/vb details; source is a directory?"""
        dst = {}
        src = 'test_dftbutils/bs'
        get_bandstructure(src, dst)
        nptest.assert_array_almost_equal(dst['bands'], self.ref_bands)
        self.assertEqual(dst['nkpts'], self.ref_nk)
        self.assertEqual(dst['nbands'], self.ref_nb)
        self.assertEqual(dst['Ef'], self.ref_Ef)
        self.assertEqual(dst['Egap'], self.ref_Eg)
        self.assertEqual(dst['Ecb'], self.ref_Ec)
        self.assertEqual(dst['Evb'], self.ref_Ev)

    def test_get_bandstructure_fileandwd(self):
        """Can we get the bandstructure and gap/cb/vb details; workdir and bands file?"""
        dst = {}
        wd = 'test_dftbutils/bs'
        get_bandstructure('bands_tot.dat', dst, wd)
        nptest.assert_array_almost_equal(dst['bands'], self.ref_bands)
        self.assertEqual(dst['nkpts'], self.ref_nk)
        self.assertEqual(dst['nbands'], self.ref_nb)
        self.assertEqual(dst['Ef'], self.ref_Ef)
        self.assertEqual(dst['Egap'], self.ref_Eg)
        self.assertEqual(dst['Ecb'], self.ref_Ec)
        self.assertEqual(dst['Evb'], self.ref_Ev)


class MeffTest(unittest.TestCase):
    """Can we extract designated effective masses from the bands."""
    def test_meff(self):
        k = np.linspace(0, 1, num=50)
        eref = k**2
        me = dftb.meff(eref, k)
        self.assertAlmostEqual(me, 0.5)
        eref = (k-0.5)**2
        me = dftb.meff(eref, k)
        self.assertAlmostEqual(me, 0.5)
if __name__ == '__main__':
    unittest.main()

