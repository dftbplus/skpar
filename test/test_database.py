"""Test operation of DB and its methods"""
import unittest
import numpy.testing as nptest
from skpar.core.database import Query, Database

class DBTest(unittest.TestCase):
    """Database test"""


    def test_database(self):
        """Can we update model DB"""
        database = Database()
        self.assertTrue(database is not None)
        #
        database.update('m1', {'i1': 42})
        self.assertDictEqual(database.all(), {'m1': {'i1': 42}})
        #
        database.update('m1', {'i1': 33})
        self.assertDictEqual(database.all(), {'m1': {'i1': 33}})
        #
        database.update('m2', {'i1': 10})
        self.assertDictEqual(database.all(), {'m1': {'i1': 33},
                                              'm2': {'i1': 10}})
        #
        database.update('m2', {'i2': 20})
        self.assertDictEqual(database.all(), {'m1': {'i1': 33},
                                              'm2': {'i1': 10,
                                                     'i2': 20}})
        #
        mdb = database.get_model('m2')
        self.assertDictEqual(mdb, {'i1': 10, 'i2': 20})
        self.assertEqual(database.get('m2', 'i2'), 20)
        #
        # check query initialised without database
        query = Query('m2', 'i1')
        self.assertEqual(query(database, atleast_1d=False), 10)
        #
        # check query initialised with database within database.query method
        self.assertEqual(database.query('m1', 'i1', atleast_1d=False), 33)
        nptest.assert_array_equal(database.query('m1', 'i1'), [33])
        #
        database.purge()
        self.assertDictEqual(database.all(), {})

if __name__ == '__main__':
    unittest.main()
