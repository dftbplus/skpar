import unittest
import logging
import numpy as np
import numpy.testing as nptest
import yaml
from skpar.core.query import Query

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)


class QueryTest(unittest.TestCase):
    """Test Query class and methods"""

    def test_query_add_modelsdb(self):
        """Can we add dictionaries to model data-base?
        """
        db1 = {}
        db3 = {'a':1, 'b':2, 'c':3}
        Query.flush_modelsdb()
        # pass a dictionary
        _db1 = Query.add_modelsdb('d1', db1)
        # get a dictionary (default, empty)
        _db2 = Query.add_modelsdb('d2')
        self.assertTrue(len(_db1.items()) == 0)
        self.assertTrue(len(_db2.items()) == 0)
        _db3 = Query.add_modelsdb('d3', db3)
        self.assertDictEqual(_db3, db3)

    def test_query_update_modelsdb(self):
        """Can we update model data-base and see update through instances?
        """
        Query.flush_modelsdb()
        d1 = Query.add_modelsdb('d1')
        d1.update({'a':1, 'b':2})
        d2 = Query.add_modelsdb('d2')
        d2.update({'a':3, 'b':4, 'c':7})
        q1 = Query('d1', 'a')
        q2 = Query(['d1', 'd2'], 'b')
        self.assertEqual(q1(), 1) 
        nptest.assert_array_equal(q2(),[2,4])

    def test_query_single_model(self):
        """Can we get data from the query of single models?
        """
        Query.flush_modelsdb()
        q1 = Query('d1', 'a')
        q2 = Query('d1', 'b')
        d1 = Query.add_modelsdb('d1')
        d1.update({'a':1, 'b':2})
        self.assertEqual(q1(), 1)
        self.assertEqual(q2(), 2)

    def test_query_multiple_models(self):
        """Can we get data from the query of multiple models?
        """
        Query.flush_modelsdb()
        modelsdb = {}
        modelsdb['d1'] = {'a':1, 'b':2}
        modelsdb['d2'] = {'a':3, 'b':4, 'c':7}
        q2 = Query(['d1', 'd2'], 'b')
        nptest.assert_array_equal(q2(modelsdb), [2,4], verbose=True)


if __name__ == '__main__':
    unittest.main()


