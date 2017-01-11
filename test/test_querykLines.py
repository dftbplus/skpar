import unittest
import logging
import numpy as np
import numpy.testing as nptest
from dftbutils import lattice
from dftbutils.querykLines import get_klines, greekLabels

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format=' %(message)s')
logger = logging.getLogger(__name__)


class QeurykLinesTest(unittest.TestCase):

    def test_get_klines(self):
        lat = lattice.FCC(3.6955*2) 
        refklines = [('X', 0), ('Gamma', 85), ('K', 175), ('L', 227), ('Gamma', 300)]
        refklinesdict = {'L': [227], 'K': [175], 'X': [0], 'Gamma': [85, 300]}
        klines, klinesdict = get_klines(lat, workdir='test_dftbutils/bs')
        self.assertListEqual(refklines, klines)
        self.assertDictEqual(refklinesdict, klinesdict)

if __name__ == '__main__':
    unittest.main()
