import unittest
import logging
import numpy as np
import numpy.testing as nptest
from skpar.dftbutils.lattice import Lattice, repr_lattice, get_dftbp_klines

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
        a = 8.9385 #1.0
        c = 12.9824 #2.0
        lat = Lattice({'type': 'TET', 'param': [a, c], 'path': 'Gamma-M-X-Gamma-Z'})
        logger.debug(lat)

    def test_orthorombic(self):
        """Orthorombic (ORC)"""
        a = 9.0714 #1.0
        b = 8.7683 #2.0
        c = 12.8024 #3.0
        #lat = Lattice({'type': 'ORC', 'param': [a, b, c], 'path': 'Gamma-S-X-Gamma-Z'})
        lat = Lattice({'type': 'ORC', 'param': [a, b, c], 'path': 'Gamma-S-Y-Gamma-Z'})
        # Default Path
        lat = Lattice({'type': 'ORC', 'param': [a, b, c]})
        logger.debug(lat)

    def test_rhombohedral(self):
        """Rhombohedral (RHL)"""
        a, angle = 5.32208613808, 55.8216166097
        lat = Lattice({'type': 'RHL', 'param': [a, angle]})
        logger.debug(lat)

    def test_monoclinic(self):
        """Monoclinic (MCL)"""
        a, b, c, angle = 5.17500, 5.17500, 5.29100, 80.78
        lat = Lattice({'type': 'MCL', 'param': [a, b, c, angle]})
        logger.debug(lat)

    def test_monoclinic_facecentered(self):
        """Face-centered Monoclinic (MCLC)"""
        a, b, c, beta = 12.23, 3.04, 5.8, 103.70
        lat = Lattice({'type': 'MCLC', 'param': [a, b, c, beta]})
        logger.debug(lat)


if __name__ == '__main__':
    unittest.main()
