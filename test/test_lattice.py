import unittest
import logging
import numpy as np
import numpy.testing as nptest
from dftbutils import lattice

class LatticeTest(unittest.TestCase):

    def test_simplecubic(self):
        """Simple cubic (CUB)"""
        a = 1.0
        lat = lattice.Lattice('CUB', a)
        lattice.repr_lattice(lat)
        lattice.get_dftbp_klines(lat)

    def test_bodycenteredcubic(self):
        """Body centered cubic (BCC)"""
        a = 1.0
        lat = lattice.Lattice('BCC', a)
        lattice.repr_lattice(lat)
        lattice.get_dftbp_klines(lat)

    def test_facecenteredcubic(self):
        """Face centered cubic (FCC)"""
        a = 1.0
        lat = lattice.Lattice('FCC', a)
        lattice.repr_lattice(lat)
        lattice.get_dftbp_klines(lat)

    def test_hexagonal(self):
        """Hexagonal (HEX)"""
        a = 1.0
        c = 2.0
        lat = lattice.Lattice('HEX', [a, c])
        lattice.repr_lattice(lat)
        lattice.get_dftbp_klines(lat)

    def test_tetragonal(self):
        """Tetragonal (TET)"""
        a = 1.0
        c = 2.0
        lat = lattice.Lattice('TET', [a, c])
        lattice.repr_lattice(lat)
        lattice.get_dftbp_klines(lat)

    def test_orthorombic(self):
        """Orthorombic (ORC)"""
        a = 1.0
        b = 2.0
        c = 3.0
        lat = lattice.Lattice('ORC', [a, b, c])
        lattice.repr_lattice(lat)
        lattice.get_dftbp_klines(lat)


if __name__ == '__main__':
    unittest.main()
