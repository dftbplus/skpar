import unittest
import logging
import numpy as np
import numpy.testing as nptest
from skpar.core.database import Database
from skpar.dftbutils import lattice
from skpar.dftbutils.lattice import Lattice
from skpar.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skpar.dftbutils.querykLines import get_klines, greekLabels, get_kvec_abscissa

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format=' %(message)s')
logger = logging.getLogger(__name__)


class QuerykLinesTest(unittest.TestCase):

    def test_get_klines(self):
        #lat = lattice.FCC(3.6955*2) 
        lat = Lattice({'type': 'FCC', 'param': 3.6955*2}) 
        refklines = [('X', 0), ('Gamma', 85), ('K', 175), ('L', 227), ('Gamma', 300)]
        refklinesdict = {'L': [227], 'K': [175], 'X': [0], 'Gamma': [85, 300]}
        klines, klinesdict = get_klines(lat, workdir='test_dftbutils/bs')
        self.assertListEqual(refklines, klines)
        self.assertDictEqual(refklinesdict, klinesdict)

class GetAbscissakVectorTest(unittest.TestCase):

    def test_get_kvec_abscissa(self):
        """Can we get the bandstructure and extract the kvector info"""
        latticeinfo = {'type': 'FCC', 'param': 1.}
        lat = Lattice(latticeinfo)
        kLines = [('L', 0), ('Gamma', 10), ('X', 20), ('U', 30), ('K', 31), ('Gamma', 41)]
        logger.debug('kLines     : {}'.format(kLines))
        xx, xt, xl = get_kvec_abscissa(lat, kLines)
        refxl = ['L', 'Γ', 'X', 'U|K', 'Γ']
        refxt = [0, 5.44140, 11.724583399882238, 13.946024868961421, 20.610349276198971]
        self.assertListEqual(xl, refxl)
        nptest.assert_almost_equal(xt, refxt, 5)
        self.assertAlmostEqual(xx[-1], xt[-1])
        self.assertEqual(len(xx), kLines[-1][-1]+1)

    def test_get_kvec_abscissa2(self):
        """Can we get the bandstructure and extract the kvector info"""
        latticeinfo = {'type': 'FCC', 'param': 1.}
        lat = Lattice(latticeinfo)
        database = Database()
        src = 'test_dftbutils/bs'
        get_bandstructure({'workroot': '.'}, database, src, 'test', latticeinfo=latticeinfo)
        kLines = database.get_item('test', 'kLines')
        bands = database.get_item('test', 'bands')
        logger.debug('Bands.shape: {}'.format(bands.shape))
        logger.debug('kLines     : {}'.format(kLines))
        xx, xt, xl = get_kvec_abscissa(lat, kLines)
        refxl = ['X', 'Γ', 'K', 'L', 'Γ']
        refxt = [0, 6.28319, 12.94751, 16.79516, 22.23656]
        self.assertListEqual(xl, refxl)
        nptest.assert_almost_equal(xt, refxt, 5)
        self.assertAlmostEqual(xx[-1], xt[-1])
        self.assertEqual(len(xx), kLines[-1][-1]+1)

    def test_get_kvec_abscissa3(self):
        """Can we get the bandstructure and extract the kvector info, from vasp style kLines"""
        latticeinfo = {'type': 'FCC', 'param': 1.}
        lat = Lattice(latticeinfo)
        kLines = [('X', 0), ('Gamma', 9), ('Gamma', 10), ('K', 19), ('K', 20), ('L', 29), ('L', 30), ('Gamma', 39)]
        xx, xt, xl = get_kvec_abscissa(lat, kLines)
        refxl = ['X', 'Γ', 'K', 'L', 'Γ']
        refxt = [0, 6.28319, 12.94751, 16.79516, 22.23656]
        self.assertListEqual(xl, refxl)
        nptest.assert_almost_equal(xt, refxt, 5)
        self.assertAlmostEqual(xx[-1], xt[-1])
        self.assertEqual(len(xx), kLines[-1][-1]+1)


if __name__ == '__main__':
    unittest.main()
