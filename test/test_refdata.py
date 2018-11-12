"""Test the operation related to reference data"""
import unittest
import numpy.testing as nptest
import yaml
from skpar.core.refdata import get_refdata, parse_refdata_input

class RefdataTest(unittest.TestCase):
    """refdata test"""

    yamldata = """reference:
        band_gap:
            doc: Band gap, Si
            data: 1.12
        evol-hydrostatic:
            doc: Energy-Volume under hydrostatic strain, Si
            data: [-23.387, -23.719, -23.974,
                   -24.158, -24.278, -24.304, -24.348, -24.309,
                   -24.228, -24.11 , -23.952]
        vband:
            doc: Valence band, Si
            source:
                file: ./reference_data/fakebands.dat
                loader_args: {unpack: True}
                process:
                    # eliminate unused columns, like k-pt enumeration
                    # indexes and ranges below refer to file, not array,
                    # i.e. independent of 'unpack' loader argument
                    # filter k-point enumeration, and bands, potentially
                    rm_columns: 1
                    # filter k-points if needed for some reason
                    # rm_rows   : [[18,36], [1,4]]
                    # for unit conversion, e.g. Hartree to eV, if needed
                    # scale     : 1
    """

    def test_parse_userinp(self):
        """Test reference input is parsed completely."""
        userinp = yaml.load(self.yamldata)['reference']
        assert isinstance(userinp, dict)
        refdb = parse_refdata_input(userinp)
        nptest.assert_array_equal([1.12], get_refdata('band_gap', refdb))
        nptest.assert_array_equal(userinp['evol-hydrostatic']['data'],
                                  get_refdata('evol-hydrostatic', refdb))


    def test_parse_refsource(self):
        """blah"""
        pass


if __name__ == '__main__':
    unittest.main()
