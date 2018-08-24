"""Test operation of DB and its methods"""
import unittest
import numpy.testing as nptest
from skpar.core.database import Query, Database, update

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
        update(database, 'm1', {'i2': 25})
        self.assertDictEqual(database.all(), {'m1': {'i1': 33,
                                                     'i2': 25},
                                              'm2': {'i1': 10,
                                                     'i2': 20}})
        database.update({'m2': {'i3': 40}})
        self.assertDictEqual(database.all(), {'m1': {'i1': 33,
                                                     'i2': 25},
                                              'm2': {'i3': 40}})
        #
        mdb = database.get('m2')
        self.assertDictEqual(mdb, {'i3': 40})
        self.assertEqual(database.get_item('m1', 'i2'), 25)
        #
        # check query initialised without database
        query = Query('m2', 'i1')
        self.assertEqual(query(database, atleast_1d=False), None)
        query = Query('m2', 'i3')
        self.assertEqual(query(database, atleast_1d=False), 40)
        #
        # check query initialised with database within database.query method
        self.assertEqual(database.query('m1', 'i1', atleast_1d=False), 33)
        nptest.assert_array_equal(database.query('m1', 'i1'), [33])
        #
        database.clear()
        self.assertDictEqual(database.all(), {})

if __name__ == '__main__':
    unittest.main()
