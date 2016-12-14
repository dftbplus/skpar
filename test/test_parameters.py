import unittest
import numpy as np
import numpy.testing as nptest
import yaml
from skopt.parameters import get_parameters

class ParametersTest(unittest.TestCase):
    """
    Verify handling of parameters
    """
    def test_get_explicit_parameters(self):
        """Can we interpret explicit parameter definitions correctly?"""
        yamldata="""parameters:
            - r0_Si_sp: 4 2 6
            - nc_Si_sp: 4 2 12 i
            - rc_O_sp:  1.5 4
            - ep_O_sp:  8 i
            """
        spec = yaml.load(yamldata)['parameters']
        params = get_parameters(spec)
        self.assertEqual(len(params), 4)
        values = [4, 4, 0, 8]
        minv = [2, 2, 1.5, None]
        maxv = [6, 12, 4, None]
        names = ['r0_Si_sp', 'nc_Si_sp', 'rc_O_sp', 'ep_O_sp']
        for i, par in enumerate(params):
            self.assertEqual(par.value, values[i])
            self.assertEqual(par.minv, minv[i])
            self.assertEqual(par.maxv, maxv[i])
            self.assertEqual(par.name, names[i])
            print (par)

if __name__ == '__main__':
    unittest.main()

