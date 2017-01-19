import unittest
import logging
import numpy as np
import numpy.testing as nptest
import yaml
from skopt.parameters import get_parameters, update_template

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)


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
        logging.debug(spec)
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
            logger.debug (par)

class TemplateTest(unittest.TestCase):
    """Test we can read, update and write the template file."""
    tmplt = """This is some file
    with a few parameters defined like this:
    # %(Dummy) or something like this.
        %(Dummy)f  # parameter name only
    And we want to get
    # 2.7 or something like this
    by putting a real value in place of %(Gummy)i
    and %(Bear)f
    """
    def test_update_template(self):
        """Can we update a template and write it to a file?"""
        yamldata="""parameters:
            - Dummy: 1.5
            - Gummy: 15 i
            - Bear : 27
            - Fear
            """
        spec = yaml.load(yamldata)['parameters']
        logging.debug(spec)
        params = get_parameters(spec)
        pardict = dict([(p.name, p.value) for p in params])
        updated = update_template(self.tmplt, pardict)
        expected = """This is some file
    with a few parameters defined like this:
    # %(Dummy) or something like this.
        1.500000  # parameter name only
    And we want to get
    # 2.7 or something like this
    by putting a real value in place of 15
    and 27.000000
    """
        self.assertEqual(updated, expected)

if __name__ == '__main__':
    unittest.main()

