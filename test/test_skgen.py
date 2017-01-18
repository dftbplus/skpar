import unittest
import logging
import numpy as np
import numpy.testing as nptest
from dftbutils.parametersSKGEN import Parameter, update_template
from dftbutils import queryDFTB as dftb

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)


class ParametersTest(unittest.TestCase):
    """Test we can declare parameters based on input spec"""
    def test_parameter_value_declaration(self):
        """Can we declare initial value?"""
        # name only
        s = "%( Name)"
        p = Parameter(s)
        logger.debug(p)
        self.assertEqual(p.name,  'Name')
        self.assertEqual(p.value,None)
        self.assertEqual(p.minv, None)
        self.assertEqual(p.maxv, None)
        # initial value only
        s = "%( name_default, 1.5)"
        p = Parameter(s)
        logger.debug(p)
        self.assertEqual(p.name,  'name_default')
        self.assertEqual(p.value, float(1.5))
        self.assertEqual(p.minv, None)
        self.assertEqual(p.maxv, None)
        # range only; check min max are handled properly!
        s = "%( name_range, 5, 4)"
        p = Parameter(s)
        logger.debug(p)
        self.assertEqual(p.name,  'name_range')
        self.assertEqual(p.value, None)
        self.assertEqual(p.minv, 4.)
        self.assertEqual(p.maxv, 5.)
        # full spec
        s = "%( new, 1.5, 2., 3.)"
        p = Parameter(s)
        logger.debug(p)
        self.assertEqual(p.name,  'new')
        self.assertEqual(p.value, float(1.5))
        self.assertEqual(p.minv,  int(2.))
        self.assertEqual(p.maxv,  int(3.))

        pass

    def test_parameter_type_declaration(self):
        """Can we control the type?"""
        # explicit int, even if we write a dot
        s = "%( int, 1., 2., 3.)i"
        p = Parameter(s)
        logger.debug(p)
        self.assertTrue(isinstance(p.value, int))
        self.assertTrue(isinstance(p.minv, int))
        self.assertTrue(isinstance(p.maxv, int))
        # explicit float, even if we omit the dot
        s = "%( float, 1, 2, 3)f"
        p = Parameter(s)
        logger.debug(p)
        self.assertTrue(isinstance(p.value, float))
        self.assertTrue(isinstance(p.minv, float))
        self.assertTrue(isinstance(p.maxv, float))
        # default float, even without dot
        s = "%( float_dflt, 1, 2, 3)"
        p = Parameter(s)
        logger.debug(p)
        self.assertTrue(isinstance(p.value, float))
        self.assertTrue(isinstance(p.minv, float))
        self.assertTrue(isinstance(p.maxv, float))

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
        p1 = Parameter('%(Dummy, 1.5)')
        p2 = Parameter('%(Gummy, 15)i')
        p3 = Parameter('%(Bear , 27.)')
        pardict = dict([(p.name, p.value) for p in [p1, p2, p3]])
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
