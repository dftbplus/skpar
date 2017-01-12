import unittest
import logging
import numpy as np
import numpy.testing as nptest
from dftbutils.lattice import Lattice, repr_lattice, get_dftbp_klines

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)


class LatticeTest(unittest.TestCase):

    def test_simplecubic(self):
        """Simple cubic (CUB)"""
        latinfo = {'type': 'CUB', 'param': 1.0}
        lat = Lattice(latinfo)
        logger.debug(lat)

    def test_bodycenteredcubic(self):
        """Body centered cubic (BCC)"""
        latinfo = {'type': 'BCC', 'param': 1.0}
        lat = Lattice(latinfo)
        logger.debug(lat)

    def test_facecenteredcubic(self):
        """Face centered cubic (FCC)"""
        latinfo = {'type': 'FCC', 'param': 1.0}
        lat = Lattice(latinfo)
        logger.debug(lat)

    def test_hexagonal(self):
        """Hexagonal (HEX)"""
        a = 1.0
        c = 2.0
        lat = Lattice({'type': 'HEX', 'param': [a, c]})
        logger.debug(lat)

    def test_tetragonal(self):
        """Tetragonal (TET)"""
        a = 1.0
        c = 2.0
        lat = Lattice({'type': 'TET', 'param': [a, c]})
        logger.debug(lat)

    def test_orthorombic(self):
        """Orthorombic (ORC)"""
        a = 1.0
        b = 2.0
        c = 3.0
        lat = Lattice({'type': 'ORC', 'param': [a, b, c]})
        logger.debug(lat)


if __name__ == '__main__':
    unittest.main()
