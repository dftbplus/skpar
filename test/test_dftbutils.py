import unittest
import logging
import numpy as np
import numpy.testing as nptest
from skpar.core.database import Database
from skpar.dftbutils.queryDFTB import DetailedOut, BandsOut, Bandstructure
from skpar.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skpar.dftbutils.queryDFTB import get_effmasses, get_special_Ek
from skpar.dftbutils.queryDFTB import get_labels
from skpar.dftbutils import queryDFTB as dftb
from math import pi

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)


class GetLabelsTest(unittest.TestCase):
    """Test helper function get_labels."""
    def test_getlabels(self):
        exp = ['Gamma', 'X']
        self.assertListEqual(exp, get_labels('GammaX'))
        self.assertListEqual(exp, get_labels('Gamma-X'))
        exp = ['P', 'Gamma']
        self.assertListEqual(exp, get_labels('PGamma'))
        self.assertListEqual(exp, get_labels('P-Gamma'))
        exp = ['Gamma', 'Sigma']
        self.assertListEqual(exp, get_labels('GammaSigma'))
        self.assertListEqual(exp, get_labels('Gamma-Sigma'))
        exp = ['L', 'K']
        self.assertListEqual(exp, get_labels('LK'))
        self.assertListEqual(exp, get_labels('L-K'))

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
        env = {}
        database = Database()
        #
        src = 'test_dftbutils/scc'
        dst = 'test.scc'
        get_dftbp_data(env, database, src, dst)
        modeldict = database.get(dst)
        self.assertDictEqual(modeldict, self.ref_scc)
        #
        src = 'test_dftbutils/bs'
        dst = 'test.bs'
        get_dftbp_data(env, database, src, dst)
        modeldict = database.get(dst)
        self.assertDictEqual(modeldict, self.ref_bs)


class BandsOutTest(unittest.TestCase):
    """Check if we can read bands_tot.dat from dp_bands."""

    ff1 = 'reference_data/fakebands.dat'
    fake_bands = np.loadtxt(ff1, unpack=True)
    # eliminate column 1, which enumerates the kpoints
    fake_bands = fake_bands[1:]
    fake_nb, fake_nk = fake_bands.shape

    ff2 = 'test_dftbutils/bs/bands_tot.dat'
    ref_bands = np.loadtxt(ff2, unpack=True)
    ref_bands = ref_bands[1:]
    ref_nb, ref_nk = ref_bands.shape
    ref_ivbtop = 15 # data is from SiO2 (2*4e(Si)  + 4*8e(O) = 32e)
    ref_Ev = np.max(ref_bands[ref_ivbtop])
    ref_Ec = np.min(ref_bands[ref_ivbtop+1])
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

    def test_get_bandstructure(self):
        """Can we get the bandstructure and gap/cb/vb details?"""
        env = {}
        database = Database()
        src = 'test_dftbutils/bs'
        dst = 'test.bs'
        get_bandstructure(env, database, src, dst)
        modeldict = database.get(dst)
        nptest.assert_array_almost_equal(modeldict['bands'], self.ref_bands)
        self.assertEqual(modeldict['nkpts'], self.ref_nk)
        self.assertEqual(modeldict['nbands'], self.ref_nb)
        self.assertEqual(modeldict['Ef'], self.ref_Ef)
        self.assertEqual(modeldict['Egap'], self.ref_Eg)
        self.assertEqual(modeldict['Ecb'], self.ref_Ec)
        self.assertEqual(modeldict['Evb'], self.ref_Ev)


class MeffTest(unittest.TestCase):
    """Can we extract designated effective masses from the bands."""
    def test_meff(self):
        k = np.linspace(0, 1, num=50)
        #
        eref = k**2
        me = dftb.meff(eref, k)
        self.assertAlmostEqual(me, 0.5)
        #
        eref = (k-0.5)**2
        me = dftb.meff(eref, k)
        self.assertAlmostEqual(me, 0.5)

    def test_get_effmasses_default(self):
        """Can we get effective masses in addition to band-structure, with default settings?"""
        env = {}
        database = Database()
        src = 'test_dftbutils/Si/bs'
        model = 'test.meff'
        get_bandstructure(env, database, src, model, latticeinfo={'type': 'FCC', 'param': 5.431})
        dst = database.get(model)
        # the values below are in oldskpar.debug.log in the above dir
        self.assertTrue(dst['withSOC'])
        self.assertEqual(dst['ivbtop'], 7)
        self.assertEqual(dst['nkpts'], 206)
        self.assertEqual(dst['nbands'], 36)
        self.assertAlmostEqual(dst['Ef'], -3.0621, places=3)
        self.assertAlmostEqual(dst['Egap'], 1.1289, places=3)
        self.assertAlmostEqual(dst['Ecb'], -3.06221, places=3)
        self.assertAlmostEqual(dst['Evb'], -4.19099, places=3)
        #
        ref_klines = [('L', 0), ('Gamma', 53), ('X', 113), ('U', 141), ('K', 142), ('Gamma', 205)]
        ref_klinesdict = {'K': [142], 'X': [113], 'Gamma': [53, 205], 'L': [0], 'U': [141]}
        self.assertListEqual(dst['kLines'], ref_klines)
        self.assertDictEqual(dst['kLinesDict'], ref_klinesdict)
        get_effmasses(env, database, model, model)
        ref_meff_tags = ['me_LG', 'me_GX', 'me_XU', 'me_KG']
        ref_meff_tags.extend(['mh_LG', 'mh_GX', 'mh_XU', 'mh_KG'])
        self.assertTrue(all([key in dst for key in ref_meff_tags]))

    def test_get_effmasses_select(self):
        """Can we get select effective masses with a control options?"""
        env = {}
        database = Database()
        model = 'test.meff'
        # NOTABENE: the refdata here is from SOC calculation!!!
        src = 'test_dftbutils/Si/bs'
        get_bandstructure(env, database, src, model, latticeinfo={'type': 'FCC', 'param': 5.431})
        dst = database.get(model)
        directions = ['Gamma-X', 'Gamma-L', 'Gamma-K']
        # Example how to extract different masses over a different energy window:
        # Note that subsequent extractions overwrite final data in dst, so we start with
        # the deepest bands, and than reduce the number of bands, towards to top of VB
        # The energy window should be adjusted depending on the anticipated curvature of the band
        get_effmasses(env, database, model, model, directions=directions, carriers='e', nb=1, Erange=0.005, usebandindex=True)
        # get the lowest band masses: (spin-orbit); forceErange seems to not work properly?
        get_effmasses(env, database, model, model, directions=directions, carriers='h', nb=5, Erange=0.0015, forceErange=True)
        # get the light hole bands (3 and 4)
        get_effmasses(env, database, model, model, directions=directions, carriers='h', nb=3, Erange=0.008)
        # get the top two (heavy hole) bands (1 and 2); enforce indexing! (i.e. add _0)
        get_effmasses(env, database, model, model, directions=directions, carriers='h', nb=1, Erange=0.002, usebandindex=True)
        self.assertAlmostEqual(dst['me_GX_0'],  0.935, places=3)
        self.assertAlmostEqual(dst['mh_GX_0'], -0.278, places=2)
        self.assertAlmostEqual(dst['mh_GK_0'], -1.891, places=3)
        self.assertAlmostEqual(dst['mh_GL_0'], -0.633, places=3)
        self.assertAlmostEqual(dst['mh_GX_2'], -0.286, places=3)
        self.assertAlmostEqual(dst['mh_GK_2'], -0.362, places=3)
        self.assertAlmostEqual(dst['mh_GL_2'], -2.2426, places=3)
        self.assertAlmostEqual(dst['mh_GX_4'], -0.1389, places=3)
        self.assertAlmostEqual(dst['mh_GK_4'], -0.095, places=3)
        self.assertAlmostEqual(dst['mh_GL_4'], -0.086, places=3)
        self.assertAlmostEqual(dst['cbminpos_GX_0'], 0.817, places=2)


class EkTest(unittest.TestCase):
    """Can we extract designated eigenvalues at special points of symmetry in the BZ?"""
    def test_get_special_Ek(self):
        """Get E(k) for k obtained from the kLines"""
        env = {}
        database = Database()
        model = 'test.Ek'
        src = 'test_dftbutils/Si/bs'
        get_bandstructure(env, database, src, model, latticeinfo={'type': 'FCC', 'param': 5.431})
        dst = database.get(model)
        get_special_Ek(env, database, model, model)
        self.assertAlmostEqual(dst['Ec_L_0'], 0.4  , places=3)
        self.assertAlmostEqual(dst['Ec_G_0'], 1.616, places=3)
        self.assertAlmostEqual(dst['Ec_X_0'], 0.2025, places=3)
        self.assertAlmostEqual(dst['Ec_U_0'], 0.6915, places=3)
        self.assertAlmostEqual(dst['Ec_K_0'], 0.6915, places=3)
        #
        self.assertAlmostEqual(dst['Ev_L_0'],-2.5016, places=3)
        self.assertAlmostEqual(dst['Ev_G_0'],-1.1289, places=3)
        self.assertAlmostEqual(dst['Ev_X_0'],-3.9592, places=3)
        self.assertAlmostEqual(dst['Ev_U_0'],-3.5885, places=3)
        self.assertAlmostEqual(dst['Ev_K_0'],-3.5885, places=3)

    def test_get_special_Ek_options(self):
        """Get E(k) for explicitly given, and multiple bands"""
        env = {}
        database = Database()
        model = 'test.Ek'
        src = 'test_dftbutils/Si/bs'
        get_bandstructure(env, database, src, model, latticeinfo={'type': 'FCC', 'param': 5.431})
        dst = database.get(model)
        get_special_Ek(env, database, model, model, sympts = ['K', 'L'], 
                        extract={'cb': [0, 2, 4, 6], 'vb': [0, 2, 4, 6]})
        self.assertAlmostEqual(dst['Ec_L_4'], 2.8089, places=3)
        self.assertAlmostEqual(dst['Ec_L_0'], 0.3995, places=3)
        self.assertAlmostEqual(dst['Ec_K_0'], 0.6915, places=3)
        #
        self.assertAlmostEqual(dst['Ev_L_0'],-2.5016, places=3)
        self.assertAlmostEqual(dst['Ev_L_4'],-7.842, places=3)
        self.assertAlmostEqual(dst['Ev_L_6'],-11.3369, places=3)
        self.assertAlmostEqual(dst['Ev_K_0'],-3.5884, places=3)
        self.assertAlmostEqual(dst['Ev_K_2'],-4.963, places=3)
        self.assertAlmostEqual(dst['Ev_K_4'],-8.694, places=3)
        self.assertAlmostEqual(dst['Ev_K_6'],-9.8759, places=3)

if __name__ == '__main__':
    unittest.main()

